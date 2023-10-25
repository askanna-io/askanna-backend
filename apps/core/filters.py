from django.db.models import Q
from django.utils.encoding import force_str
from django_filters import BaseInFilter, CharFilter
from rest_framework.compat import coreapi, coreschema
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter as BaseOrderingFilter


class MultiValueCharFilter(BaseInFilter, CharFilter):
    pass


class MultiUpperValueCharFilter(BaseInFilter, CharFilter):
    def filter(self, qs, value):
        if not value:
            # No point filtering if empty
            return qs

        upper_values = []

        for v in value:
            upper_values.append(v.upper())

        return super().filter(qs, upper_values)


def case_insensitive(queryset, name, value):
    if isinstance(value, str):
        return queryset.filter(**{f"{name}__iexact": value})

    q = Q()
    for v in value:
        q |= Q(**{f"{name}__iexact": v})

    return queryset.filter(q)


def filter_multiple(queryset, name, value):
    values = list(map(lambda x: x.strip(), value.split(",")))
    field_name = f"{name}__in"
    return queryset.filter(**{field_name: values})


def filter_array(queryset, name, value):
    """
    Create  {field}__contains=[{"subfield": "value"}] lookup.

    Example: CharFilter(field_name="{field}__*__{subfield}", method="filter_array")
    """
    field = name.split("__*__")[0]
    subfield = name.split("__*__")[1]
    return queryset.filter(**{f"{field}__contains": [{subfield: value}]})


class OrderingFilter(BaseOrderingFilter):
    ordering_param = "order_by"
    ordering = "-created_at"
    ordering_fields = ["created_at", "modified_at"]
    ordering_description = (
        "Order the list by one or more fields from the available values. Use a minus sign to "
        "reverse the order. When order by multiple fields, separate them with a comma."
    )

    def get_ordering(self, request, queryset, view):
        """
        Ordering is set by a comma delimited ?order_by=... query parameter.
        """
        ordering_fields = self.get_default_ordering(view)

        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(",")]

            if fields:
                self.validate_fields(queryset, fields, view, request)
                ordering_fields = self.replace_field_aliases(fields, view)

        return [field.replace(".", "__") for field in ordering_fields]

    def replace_field_aliases(self, fields, view):
        """
        Replace field aliases with the actual field name.
        """
        field_aliases = getattr(view, "ordering_fields_aliases", None)

        if field_aliases:
            for item in fields:
                reverse = True if item.startswith("-") else False
                if item.lstrip("-") in field_aliases.keys():
                    new_value = field_aliases[item.lstrip("-")]
                    if reverse:
                        new_value = "-" + new_value
                    fields[fields.index(item)] = new_value

        return fields

    def validate_fields(self, queryset, fields, view, request):
        """
        Validate that the fields being ordered by are in the list 'ordering_fields'.
        """

        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {"request": request})]

        def is_field_valid(field):
            if field.startswith("-"):
                field = field[1:]
            return field in valid_fields

        for field in fields:
            if not is_field_valid(field):
                raise ValidationError({"order_by": f"Invalid ordering field: {field}"})

    def get_default_ordering(self, view):
        """
        Return the default ordering used by the view.
        """
        ordering = getattr(view, "ordering", self.ordering)
        if isinstance(ordering, str):
            return (ordering,)
        return ordering

    def get_ordering_description(self, view):
        """
        Return a description for the order by parameter. This description includes the available values and
        information about the default ordering.
        """
        description = getattr(view, "ordering_description", self.ordering_description)

        default_ordering = self.get_default_ordering(view)
        ordering_fields = getattr(view, "ordering_fields", self.ordering_fields)

        if default_ordering and ordering_fields:
            description += (
                "<p><i>Default ordering:</i> "
                + ", ".join(default_ordering)
                + "</br><i>Available values:</i> "
                + ", ".join(ordering_fields)
                + "</p>"
            )
        elif default_ordering:
            description += "<p><i>Default ordering:</i> " + ", ".join(default_ordering) + "</p>"
        elif ordering_fields:
            description += "<p><i>Available values:</i> " + ", ".join(ordering_fields) + "</p>"

        return description

    def get_schema_fields(self, view):
        assert coreapi is not None, "coreapi must be installed to use `get_schema_fields()`"
        assert coreschema is not None, "coreschema must be installed to use `get_schema_fields()`"

        ordering_description = self.get_ordering_description(view)

        return [
            coreapi.Field(
                name=self.ordering_param,
                required=False,
                location="query",
                schema=coreschema.String(
                    title=force_str(self.ordering_title), description=force_str(ordering_description)
                ),
            )
        ]

    def get_schema_operation_parameters(self, view):
        ordering_description = self.get_ordering_description(view)

        return [
            {
                "name": self.ordering_param,
                "required": False,
                "in": "query",
                "description": force_str(ordering_description),
                "schema": {"type": "string"},
            },
        ]
