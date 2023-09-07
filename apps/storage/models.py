from django.db import models

from core.models import NameDescriptionBaseModel, ObjectReference


def get_upload_file_to(instance, filename):
    if instance.upload_to is None:
        return filename

    return f"{instance.upload_to}/{filename}"


class FileQuerySet(models.QuerySet):
    def active(self, add_select_related=False):
        active_query = self.filter(
            deleted_at__isnull=True,
            _created_for__account_user__deleted_at__isnull=True,
            _created_for__account_membership__deleted_at__isnull=True,
        ).select_related(
            "_created_for__account_user",
            "_created_for__account_membership__user",
        )

        if add_select_related:
            return active_query.select_related(
                "_created_by__account_user",
                "_created_by__account_membership__user",
            )

        return active_query


class FileManager(models.Manager):
    def create(self, **kwargs):
        if "created_for" in kwargs:
            kwargs["_created_for"], _ = ObjectReference.get_or_create(kwargs.pop("created_for"))

        if "created_by" in kwargs:
            kwargs["_created_by"], _ = ObjectReference.get_or_create(kwargs.pop("created_by"))

        return super().create(**kwargs)

    def filter(self, **filter_args):
        created_for_key = "created_for"
        created_by_key = "created_by"

        if created_for_key in filter_args:
            filter_args["_created_for"] = ObjectReference.get_or_create(filter_args.pop(created_for_key))[0]

        if created_by_key in filter_args:
            filter_args["_created_by"] = ObjectReference.get_or_create(filter_args.pop(created_by_key))[0]

        return super().filter(**filter_args)


class File(NameDescriptionBaseModel):
    file = models.FileField(upload_to=get_upload_file_to)

    _created_for = models.ForeignKey(
        ObjectReference, on_delete=models.CASCADE, related_name="file_created_for", db_column="created_for"
    )
    _created_by = models.ForeignKey(
        ObjectReference, on_delete=models.CASCADE, related_name="file_created_by", db_column="created_by"
    )

    # We use the property upload_to to have the option to dynamically set the upload_to path when uploading a file
    _upload_to = None

    objects = FileManager.from_queryset(FileQuerySet)()

    def __str__(self):
        return f"{self.name or self.file.name} ({self.suuid})"

    @property
    def upload_to(self):
        return self._upload_to

    @upload_to.setter
    def upload_to(self, value):
        self._upload_to = value

    @property
    def created_for(self):
        return self._created_for.object

    @property
    def created_by(self):
        return self._created_by.object

    def request_has_object_read_permission(self, request) -> bool:
        method_name = "request_has_object_read_permission"
        assert hasattr(
            self.created_for, method_name
        ), f"Model '{self._created_for.object_type}' does not have a method '{method_name}'."

        return getattr(self.created_for, method_name)(request)
