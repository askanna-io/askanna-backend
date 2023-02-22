import os
import uuid as _uuid

from django.db import models
from django.utils import timezone
from django_cryptography.fields import encrypt
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField

from .utils.suuid import create_suuid


class DeletedModel(models.Model):
    """
    DeletedModel is an abstract base class model that provides a field to registere when the model is (soft-)deleted
    """

    deleted_at = models.DateTimeField(blank=True, auto_now_add=False, auto_now=False, null=True)

    def to_deleted(self):
        if self.deleted_at:
            return

        self.deleted_at = timezone.now()
        self.save(
            update_fields=[
                "deleted_at",
                "modified_at",
            ]
        )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    TimeStampedModel is an abstract base class model that provides self-managed "created_at" and "modified_at" fields.
    """

    created_at = CreationDateTimeField()
    modified_at = ModificationDateTimeField()

    def save(self, **kwargs):
        self.update_modified = kwargs.pop("update_modified", getattr(self, "update_modified", True))
        super().save(**kwargs)

    class Meta:
        get_latest_by = "modified_at"
        abstract = True


class DescriptionModel(models.Model):
    """
    DescriptionModel

    An abstract base class model that provides a description field.
    """

    description = models.TextField(blank=True, null=False, default="")

    class Meta:
        abstract = True


class NameModel(models.Model):
    """
    NameModel

    An abstract base class model that provides a name field.
    """

    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class NameDescriptionModel(NameModel, DescriptionModel):
    class Meta:
        abstract = True


class SlimBaseModel(TimeStampedModel, DeletedModel, models.Model):
    uuid = models.UUIDField(primary_key=True, default=_uuid.uuid4, editable=False, verbose_name="UUID")
    suuid = models.CharField(max_length=32, unique=True, editable=False, verbose_name="SUUID")

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = _uuid.uuid4()
        if not self.suuid and self.uuid:
            self.suuid = create_suuid(uuid=self.uuid)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class SlimBaseForAuthModel(SlimBaseModel):
    uuid = models.UUIDField(db_index=True, editable=False, default=_uuid.uuid4, verbose_name="UUID")

    class Meta:
        abstract = True


class BaseModel(NameDescriptionModel, SlimBaseModel):
    class Meta:
        abstract = True
        ordering = ["-modified_at"]


class AuthorModel(models.Model):
    """
    Adding created_by to the model to register who created this instance
    """

    created_by = models.ForeignKey("account.User", on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        abstract = True


class ArtifactModelMixin:
    """
    Providing basic accessors to the file on the filesystem related to the model
    """

    filetype = "file"
    filextension = "justafile"
    filereadmode = "r"
    filewritemode = "w"

    @property
    def storage_location(self):
        return self.get_storage_location()

    def get_storage_location(self):
        raise NotImplementedError(f"Please implement 'get_storage_location' for {self.__class__.__name__}")

    def get_base_path(self):
        raise NotImplementedError(f"Please implement 'get_full_path' for {self.__class__.__name__}")

    def get_full_path(self):
        raise NotImplementedError(f"Please implement 'get_base_path' for {self.__class__.__name__}")

    @property
    def stored_path(self):
        return self.get_full_path()

    @property
    def filename(self):
        return "{}_{}.{}".format(self.filetype, self.uuid.hex, self.filextension)

    def get_name(self):
        return self.filename

    @property
    def read(self):
        with open(self.stored_path, self.filereadmode) as f:
            return f.read()

    def write(self, stream):
        """
        Write contents to the filesystem
        """
        os.makedirs(self.get_base_path(), exist_ok=True)
        with open(self.stored_path, self.filewritemode) as f:
            f.write(stream.read())

    def prune(self):
        try:
            os.remove(self.stored_path)
        except FileNotFoundError:
            pass


class Setting(SlimBaseModel):
    name = models.CharField(max_length=32, blank=True, unique=True)
    value = encrypt(models.TextField(default=None, blank=True, null=True))
