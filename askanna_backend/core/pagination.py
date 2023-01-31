import inspect
from base64 import b64decode, b64encode
from collections import OrderedDict, namedtuple
from typing import Union
from urllib import parse

from core.utils.model import field_is_of_type_char
from django.db.models import F, Q, Value
from django.db.models.functions import Lower
from django.utils.encoding import force_str
from django.utils.inspect import method_has_no_args
from rest_framework import pagination
from rest_framework.compat import coreapi, coreschema
from rest_framework.exceptions import NotFound
from rest_framework.pagination import _positive_int
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

Cursor = namedtuple("Cursor", ["position", "created", "offset", "reverse"])
Position = namedtuple("Position", ["value", "is_reversed", "attr", "type_is_char"])


class CursorPagination(pagination.CursorPagination):
    """
    CursorPagination is based on the Django REST Framework CursorPagination configuration:
    - https://www.django-rest-framework.org/api-guide/pagination/
    - https://github.com/encode/django-rest-framework/blob/master/rest_framework/pagination.py

    In our implementation we add created to the ordering as an alternative for the offset. The Django REST Framework
    CursorPagination uses only offset in case there are multiple values with the same cursor position.

    With our implementation it is possible to also order by and paginate on a field such as 'name' where we expect
    many values with the same 'name'. In this case we should keep in mind that we might need to add additional indexes
    on the database table to get a good performance of the queries.

    For CursorPagination we always apply ordering. The default ordering is '-created'. The ordering applied is case
    insensitive.
    """

    page_size = 25
    max_page_size = 100
    page_size_query_param = "page_size"
    ordering = "-created"
    ordering_fields = ["created", "modified"]

    def get_default_page_size(self, view):
        """
        Return the default page size used by the view.
        """
        return getattr(view, "page_size", self.page_size)

    def get_max_page_size(self, view):
        """
        Return the max page size used by the view.
        """
        return getattr(view, "max_page_size", self.max_page_size)

    def get_page_size(self, request, view=None):
        if view:
            default_page_size = self.get_default_page_size(view)
            max_page_size = self.get_max_page_size(view)
        else:
            default_page_size = self.page_size
            max_page_size = self.max_page_size

        try:
            return _positive_int(
                request.query_params[self.page_size_query_param],
                strict=True,
                cutoff=max_page_size,
            )
        except (KeyError, ValueError):
            return _positive_int(
                default_page_size,
                strict=True,
                cutoff=max_page_size,
            )

    def paginate_queryset(self, queryset, request, view=None) -> list:
        self.base_url = request.build_absolute_uri()
        self.page_size = self.get_page_size(request, view)
        assert (
            self.page_size is not None
        ), "Using cursor pagination, but no page_size attribute was declared on the pagination class."

        # Count the queryset before applying filters used for pagination.
        self.count = self.get_count(queryset)

        self.ordering = self.get_ordering(request, queryset, view)
        if "created" not in self.ordering and "-created" not in self.ordering:
            ordering_list = list(self.ordering)
            ordering_list.append("-created")
            self.ordering = tuple(ordering_list)

        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            position_attr = self.ordering[0].lstrip("-")

            self.cursor = Cursor(
                position=Position(
                    value=None,
                    is_reversed=self.ordering[0].startswith("-"),
                    attr=position_attr,
                    type_is_char=field_is_of_type_char(queryset.model, position_attr),
                ),
                created=None,
                offset=0,
                reverse=False,
            )

        # Cursor pagination always enforces an ordering
        queryset = self.order_queryset(queryset)

        # If the position is a char field we need to apply a lower function to the position field because ordering is
        # case insensitive.
        if self.cursor.position.type_is_char is True:
            queryset = queryset.annotate(
                lower_position=Lower(self.cursor.position.attr),
            )

        # If we have a cursor, filter the queryset based on the cursor.
        if self.cursor.position.value is not None or self.cursor.created is not None:
            queryset = self.filter_cursor_queryset(queryset)

        # If we have an offset cursor then offset the entire page by that amount. We also always fetch an extra item
        # in order to determine if there is a page following on from this one.
        results = list(queryset[self.cursor.offset : self.cursor.offset + self.page_size + 1])
        self.page = list(results[: self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(results[-1])
            following_created = results[-1].created
        else:
            has_following_position = False
            following_position = None
            following_created = None

        if self.cursor.reverse:
            # If we have a reverse queryset, then the query ordering was in reverse so we need to reverse the items
            # again before returning them to the user.
            self.page = list(reversed(self.page))

            # Determine next and previous positions for reverse cursors.
            self.has_next = (
                self.cursor.position.value is not None or self.cursor.created is not None or self.cursor.offset != 0
            )
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = self.cursor.position.value
                self.next_created = self.cursor.created
            if self.has_previous:
                self.previous_position = following_position
                self.previous_created = following_created
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (
                self.cursor.position.value is not None or self.cursor.created is not None or self.cursor.offset != 0
            )
            if self.has_next:
                self.next_position = following_position
                self.next_created = following_created
            if self.has_previous:
                self.previous_position = self.cursor.position.value
                self.previous_created = self.cursor.created

        return self.page

    def order_queryset(self, queryset):
        """
        Apply ordering to the queryset with the following rules:

        1.  If the field is a char or text field then we apply a case insensitive ordering.
        2.  When ordering is descending we make sure that null values are at the start of the list.
        3.  When ordering is ascending we make sure that null values are at the end of the list.
        """
        ordering_list = []

        for field in self.ordering:
            if self.cursor and self.cursor.reverse is True:
                # We are in reverse mode, so we need to reverse the ordering of each field.
                field = field[1:] if field.startswith("-") else "-" + field

            if field_is_of_type_char(queryset.model, field.lstrip("-")):
                if field.startswith("-"):
                    ordering_list.append(Lower(field[1:]).desc(nulls_first=True))
                else:
                    ordering_list.append(Lower(field).asc(nulls_last=True))
            else:
                if field.startswith("-"):
                    ordering_list.append(F(field[1:]).desc(nulls_first=True))
                else:
                    ordering_list.append(F(field).asc(nulls_last=True))

        return queryset.order_by(*ordering_list)

    def filter_cursor_queryset(self, queryset):
        """
        Filter the queryset based on the cursor. To support filtering on fields that don't have to be unique and that
        can contain 'null' values there is a decision tree to check which filter we need to apply. This function
        contains the logic which filters to apply.

        For filtering the queryset, we have a couple of assumptions:
        1.  The position is not unique and can contain 'null' values.
        2.  Ordering the position ascending and position containing 'null' values, we assume that the 'null' values
            are at the end of the list.
        3.  The created field has no 'null' values.

        When to include 'null' values in the filter:
            The position can contain 'null' values. The get these values we need to include the 'null' values in the
            filter, but not always. If we need to include null values depends on the requested ordering. If cursor
            reverse and position ordering are the same, we need to include null values. If the cursor reversed and
            position ordering reversed are the same, then we need to include 'null' values.

            This is related to the assumption that the 'null' values are at the end of the list when ordering
            ascending. For example if we order ascending, the cursor is reversed and the position is not None, then
            the 'null' values are excluded based on the requested reversed ordering.
        """
        assert self.cursor is not None, "The cursor bust be set before filtering the queryset."
        position_value = None if self.cursor.position.value == "None" else self.cursor.position.value

        created_is_reversed = None
        if self.cursor.created:
            for i, order_item in enumerate(self.ordering):
                if i > 0 and order_item in {"created", "-created"}:
                    created_is_reversed = order_item.startswith("-")
                    break

            if created_is_reversed is None:
                raise ValueError("'created' or '-created' is not in the ordering. The cursor requires this.")

        if position_value is None and self.cursor.created is None:
            raise ValueError(
                "Cursor position and created are both 'None'. If position is 'None' then created should be set."
            )

        if self.cursor.created is None:
            if self.cursor.reverse != self.cursor.position.is_reversed:
                if self.cursor.position.type_is_char is True:
                    queryset = queryset.filter(lower_position__lt=Lower(Value(position_value)))
                else:
                    queryset = queryset.filter(**{self.cursor.position.attr + "__lt": position_value})
            else:
                if self.cursor.position.type_is_char is True:
                    queryset = queryset.filter(
                        Q(lower_position__gt=Lower(Value(position_value)))
                        | Q(**{self.cursor.position.attr + "__isnull": True})
                    )
                else:
                    queryset = queryset.filter(
                        Q(**{self.cursor.position.attr + "__gt": position_value})
                        | Q(**{self.cursor.position.attr + "__isnull": True})
                    )
        else:
            if self.cursor.reverse != created_is_reversed:
                if position_value and self.cursor.reverse != self.cursor.position.is_reversed:
                    if self.cursor.position.type_is_char is True:
                        queryset = queryset.filter(
                            Q(lower_position__lt=Lower(Value(position_value)))
                            | Q(lower_position=Lower(Value(position_value)), created__lt=self.cursor.created)
                        )
                    else:
                        queryset = queryset.filter(
                            Q(**{self.cursor.position.attr + "__lt": position_value})
                            | Q(**{self.cursor.position.attr: position_value, "created__lt": self.cursor.created})
                        )
                elif position_value:
                    if self.cursor.position.type_is_char is True:
                        queryset = queryset.filter(
                            Q(lower_position__gt=Lower(Value(position_value)))
                            | Q(lower_position=Lower(Value(position_value)), created__lt=self.cursor.created)
                            | Q(**{self.cursor.position.attr + "__isnull": True})
                        )
                    else:
                        queryset = queryset.filter(
                            Q(**{self.cursor.position.attr + "__gt": position_value})
                            | Q(**{self.cursor.position.attr: position_value, "created__lt": self.cursor.created})
                            | Q(**{self.cursor.position.attr + "__isnull": True})
                        )
                elif self.cursor.reverse != self.cursor.position.is_reversed:
                    queryset = queryset.filter(
                        Q(**{self.cursor.position.attr + "__isnull": False})
                        | Q(**{self.cursor.position.attr + "__isnull": True, "created__lt": self.cursor.created})
                    )
                else:
                    queryset = queryset.filter(
                        Q(**{self.cursor.position.attr + "__isnull": True, "created__lt": self.cursor.created})
                    )
            else:
                if position_value and self.cursor.reverse != self.cursor.position.is_reversed:
                    if self.cursor.position.type_is_char is True:
                        queryset = queryset.filter(
                            Q(lower_position__lt=Lower(Value(position_value)))
                            | Q(lower_position=Lower(Value(position_value)), created__gt=self.cursor.created)
                        )
                    else:
                        queryset = queryset.filter(
                            Q(**{self.cursor.position.attr + "__lt": position_value})
                            | Q(**{self.cursor.position.attr: position_value, "created__gt": self.cursor.created})
                        )
                elif position_value:
                    if self.cursor.position.type_is_char is True:
                        queryset = queryset.filter(
                            Q(lower_position__gt=Lower(Value(position_value)))
                            | Q(lower_position=Lower(Value(position_value)), created__gt=self.cursor.created)
                            | Q(**{self.cursor.position.attr + "__isnull": True})
                        )
                    else:
                        queryset = queryset.filter(
                            Q(**{self.cursor.position.attr + "__gt": position_value})
                            | Q(**{self.cursor.position.attr: position_value, "created__gt": self.cursor.created})
                            | Q(**{self.cursor.position.attr + "__isnull": True})
                        )
                elif self.cursor.reverse != self.cursor.position.is_reversed:
                    queryset = queryset.filter(
                        Q(**{self.cursor.position.attr + "__isnull": False})
                        | Q(**{self.cursor.position.attr + "__isnull": True, "created__gt": self.cursor.created})
                    )
                else:
                    queryset = queryset.filter(
                        Q(**{self.cursor.position.attr + "__isnull": True, "created__gt": self.cursor.created})
                    )

        return queryset

    def get_ordering(self, request, queryset, view):
        """
        Return a tuple of strings, that may be used in an `order_by` method.
        """
        ordering = self.ordering

        ordering_filters = [
            filter_cls for filter_cls in getattr(view, "filter_backends", []) if hasattr(filter_cls, "get_ordering")
        ]

        if ordering_filters:
            # If a filter exists on the view that implements `get_ordering` then we defer to that filter to determine
            # the ordering. If the filter returns None, then we use the default ordering.
            filter_cls = ordering_filters[0]
            filter_instance = filter_cls()
            ordering = filter_instance.get_ordering(request, queryset, view) or self.ordering

        assert (
            ordering is not None
        ), "Using cursor pagination, but no ordering attribute was declared on the pagination class."
        assert isinstance(
            ordering, (str, list, tuple)
        ), f"Invalid ordering. Expected string, list or tuple, but got {type(ordering).__name__}"
        assert "__" not in ordering, (
            "Cursor pagination does not support double underscore lookups for orderings. Orderings should be an "
            "unchanging, unique or nearly-unique field on the model, such as '-created' or 'pk'."
        )

        if isinstance(ordering, str):
            return (ordering,)
        return tuple(ordering)

    def get_count(self, queryset) -> int:
        """Return the total number of objects"""
        count = getattr(queryset, "count", None)
        if callable(count) and not inspect.isbuiltin(count) and method_has_no_args(count):
            return count()
        else:
            return len(queryset)

    def _get_position_from_instance(self, instance) -> str:
        assert self.cursor is not None, "Cursor must be set before calling this method."
        field_name = self.cursor.position.attr if self.cursor.position.type_is_char is False else "lower_position"

        if isinstance(instance, dict):
            attr = instance[field_name]
        elif "__" in field_name:
            attr = self._get_position_from_nested_instance(instance, field_name)

        if not "attr" in locals() or attr is None:
            attr = getattr(instance, field_name)

        return str(attr)

    def _get_position_from_nested_instance(self, instance, field_name):
        for i in range(len(field_name.split("__")) - 1):
            instance = getattr(instance, field_name.split("__")[i])
            try:
                attr = getattr(instance, field_name.split("__")[i + 1])
            except AttributeError:
                return None

        return attr  # type: ignore

    def get_next_link(self) -> Union[str, None]:
        if not self.has_next:
            return None

        assert self.cursor is not None, "To get the next link, an initial cursor should be set."

        if self.page and self.cursor.reverse and self.cursor.offset != 0:
            # If we're reversing direction and we have an offset cursor then we cannot use the first position we find
            # as a marker.
            compare_position = self._get_position_from_instance(self.page[-1])
            compare_created = self.page[-1].created
        else:
            compare_position = str(self.next_position)
            compare_created = self.next_created

        created = None
        offset = 0

        has_item_with_unique_cursor = False
        for item in reversed(self.page):
            position = self._get_position_from_instance(item)
            if position != compare_position:
                # The item in this position and the item following it have different positions.
                # We can use this position as our marker.
                has_item_with_unique_cursor = True
                if position == "None":
                    created = item.created
                break

            compare_position = position

            if self.ordering[0].lstrip("-") != "created":
                # If the page is first ordered by created, then created is equal to position. It does not add value to
                # also check and set the created value as part of the cursor.
                created = item.created
                if created != compare_created:
                    # The item in this position and the item following it have different created. We can use this
                    # position as our marker.
                    has_item_with_unique_cursor = True
                    break

                compare_created = created

            # The item in this position has the same position and created as the item following it, we can't use it as
            # a marker position, so increment the offset and keep seeking to the previous item.
            offset += 1

        if self.page and not has_item_with_unique_cursor:
            # There were no unique positions in the page.
            if not self.has_previous:
                # We are on the first page.
                # Our cursor will have an offset equal to the page size, but no position to filter against yet.
                position = None
                created = None
                offset = self.page_size
            elif self.cursor.reverse:
                # The change in direction will introduce a paging artifact, where we end up skipping forward a few
                # extra items.
                position = self.previous_position
                created = self.previous_created
                offset = 0
            else:
                # Use the position and created from the existing cursor and increment it's offset by the page size.
                position = self.previous_position
                created = self.previous_created
                offset = self.cursor.offset + self.page_size

        if not self.page:
            position = self.next_position
            created = self.next_created

        cursor = Cursor(
            position=Position(
                value=position,  # type: ignore
                is_reversed=self.cursor.position.is_reversed,
                attr=self.cursor.position.attr,
                type_is_char=self.cursor.position.type_is_char,
            ),
            created=created,
            offset=offset,
            reverse=False,
        )
        return self.encode_cursor(cursor)

    def get_previous_link(self) -> Union[str, None]:
        if not self.has_previous:
            return None

        assert self.cursor is not None, "To get the previous link, an initial cursor should be set."

        if self.page and not self.cursor.reverse and self.cursor.offset != 0:
            # If we're reversing direction and we have an offset cursor then we cannot use the first position we find
            # as a marker.
            compare_position = self._get_position_from_instance(self.page[0])
            compare_created = self.page[0].created
        else:
            compare_position = str(self.previous_position)
            compare_created = self.previous_created

        created = None
        offset = 0

        has_item_with_unique_cursor = False
        for item in self.page:
            position = self._get_position_from_instance(item)
            if position != compare_position:
                # The item in this position and the item following it have different positions.
                # We can use this position as our marker.
                has_item_with_unique_cursor = True
                if position == "None":
                    created = item.created
                break

            compare_position = position

            if self.ordering[0].lstrip("-") != "created":
                # If the page is first ordered by created, then created is equal to position. It does not add value to
                # also check and set the created value as part of the cursor.
                created = item.created
                if created != compare_created:
                    # The item in this position and the item following it have different created.
                    # We can use this position as our marker.
                    has_item_with_unique_cursor = True
                    break

                compare_created = created

            # The item in this position has the same position as the item following it, we can't use it as a marker
            # position, so increment the offset and keep seeking to the previous item.
            offset += 1

        if self.page and not has_item_with_unique_cursor:
            # There were no unique positions in the page.
            if not self.has_next:
                # We are on the final page.
                # Our cursor will have an offset equal to the page size, but no position to filter against yet.
                position = None
                created = None
                offset = self.page_size
            elif self.cursor.reverse:
                # Use the position from the existing cursor and increment it's offset by the page size.
                position = self.next_position
                created = self.next_created
                offset = self.cursor.offset + self.page_size
            else:
                # The change in direction will introduce a paging artifact, where we end up skipping back a few
                # extra items.
                position = self.next_position
                created = self.next_created
                offset = 0

        if not self.page:
            position = self.previous_position
            created = self.previous_created

        cursor = Cursor(
            position=Position(
                value=position,  # type: ignore
                is_reversed=self.cursor.position.is_reversed,
                attr=self.cursor.position.attr,
                type_is_char=self.cursor.position.type_is_char,
            ),
            created=created,
            offset=offset,
            reverse=True,
        )
        return self.encode_cursor(cursor)

    def decode_cursor(self, request) -> Union[Cursor, None]:
        """
        Given a request with a cursor, return a `Cursor` instance.
        """
        # Determine if we have a cursor, and if so then decode it.
        encoded = request.query_params.get(self.cursor_query_param)
        if encoded is None:
            return None

        try:
            query_string = b64decode(encoded.encode("ascii")).decode("ascii")
            query_dict = parse.parse_qs(query_string, keep_blank_values=True)

            position_value = query_dict.get("pv", [None])[0]
            position_is_reversed = query_dict.get("pr", [None])[0]
            position_is_reversed = bool(int(position_is_reversed)) if position_is_reversed else None
            position_attr = query_dict.get("pa", [None])[0]
            position_type_is_char = query_dict.get("pc", [None])[0]
            position_type_is_char = bool(int(position_type_is_char)) if position_type_is_char else None

            created = query_dict.get("c", [None])[0]

            offset = query_dict.get("o", ["0"])[0]
            offset = _positive_int(offset, cutoff=self.offset_cutoff)

            reverse = query_dict.get("r", ["0"])[0]
            reverse = bool(int(reverse))
        except (TypeError, ValueError):
            raise NotFound(self.invalid_cursor_message)

        return Cursor(
            position=Position(
                value=position_value,
                is_reversed=position_is_reversed,
                attr=position_attr,
                type_is_char=position_type_is_char,
            ),
            created=created,
            offset=offset,
            reverse=reverse,
        )

    def encode_cursor(self, cursor: Cursor) -> str:
        """
        Given a Cursor instance, return an url with encoded cursor.
        """
        query_dict = {}
        if cursor.position.value is not None:
            query_dict["pv"] = cursor.position.value
        if cursor.position.is_reversed is not None:
            query_dict["pr"] = "1" if cursor.position.is_reversed else "0"
        if cursor.position.attr is not None:
            query_dict["pa"] = cursor.position.attr
        if cursor.position.type_is_char is not None:
            query_dict["pc"] = "1" if cursor.position.type_is_char else "0"
        if cursor.created is not None:
            query_dict["c"] = cursor.created
        if cursor.offset != 0:
            query_dict["o"] = str(cursor.offset)
        if cursor.reverse:
            query_dict["r"] = "1"

        query_string = parse.urlencode(query_dict, doseq=True)
        query_encoded = b64encode(query_string.encode("ascii")).decode("ascii")

        return replace_query_param(self.base_url, self.cursor_query_param, query_encoded)

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "example": 123,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://localhost:8000/v1/endpoint/?cursor=123",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://localhost:8000/v1/endpoint/?cursor=123",
                },
                "results": schema,
            },
        }

    def get_page_size_description(self, view):
        description = self.page_size_query_description

        if self.get_max_page_size(view) is not None:
            description += (
                "<p><i>Default value: "
                + str(
                    _positive_int(
                        self.get_default_page_size(view),
                        strict=True,
                        cutoff=self.get_max_page_size(view),
                    )
                )
                + "</br>Maximum value: "
                + str(self.get_max_page_size(view))
                + "</i></p>"
            )

        return description

    def get_schema_fields(self, view):
        assert coreapi is not None, "coreapi must be installed to use `get_schema_fields()`"
        assert coreschema is not None, "coreschema must be installed to use `get_schema_fields()`"
        fields = [
            coreapi.Field(
                name=self.cursor_query_param,
                required=False,
                location="query",
                schema=coreschema.String(title="Cursor", description=force_str(self.cursor_query_description)),
            )
        ]
        if self.page_size_query_param is not None:
            fields.append(
                coreapi.Field(
                    name=self.page_size_query_param,
                    required=False,
                    location="query",
                    schema=coreschema.Integer(
                        title="Page size", description=force_str(self.get_page_size_description(view))
                    ),
                )
            )
        return fields

    def get_schema_operation_parameters(self, view):
        parameters = [
            {
                "name": self.cursor_query_param,
                "required": False,
                "in": "query",
                "description": force_str(self.cursor_query_description),
                "schema": {
                    "type": "string",
                },
            }
        ]
        if self.page_size_query_param is not None:
            parameters.append(
                {
                    "name": self.page_size_query_param,
                    "required": False,
                    "in": "query",
                    "description": force_str(self.get_page_size_description(view)),
                    "schema": {
                        "type": "integer",
                    },
                }
            )
        return parameters
