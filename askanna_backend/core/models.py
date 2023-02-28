import os
import uuid as _uuid

from core.fields import CreationDateTimeField, ModificationDateTimeField
from django.db import models
from django.utils import timezone
from django_cryptography.fields import encrypt

from .utils.suuid import create_suuid


class BaseModel(models.Model):
    """
    BaseModel is an abstract base class model that provides the fields:
     - uuid
     - suuid
     - created_at
     - modified_at
     - deleted_at

    "created_at" and "modified_at" are self-managed fields that are automatically set to the current date/time when the
    model is created or updated.

    "deleted_at" is used to mark the model as deleted, but not actually delete it from the database.
    """

    uuid = models.UUIDField(primary_key=True, default=_uuid.uuid4, editable=False, verbose_name="UUID")
    suuid = models.CharField(max_length=32, unique=True, editable=False, verbose_name="SUUID")

    created_at = CreationDateTimeField()
    modified_at = ModificationDateTimeField()

    deleted_at = models.DateTimeField(blank=True, auto_now_add=False, auto_now=False, null=True)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = _uuid.uuid4()
        if not self.suuid and self.uuid:
            self.suuid = create_suuid(uuid=self.uuid)

        self.update_modified = kwargs.pop("update_modified", getattr(self, "update_modified", True))
        super().save(*args, **kwargs)

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
        get_latest_by = "modified_at"
        ordering = ["-modified_at"]


class NameDescriptionBaseModel(BaseModel):
    """
    NameDescriptionBaseModel is an abstract base class model that provides the fields:
     - uuid
     - suuid
     - name
     - description
     - created_at
     - modified_at
     - deleted_at
    """

    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=False, default="")

    class Meta:
        abstract = True


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


class Setting(BaseModel):
    name = models.CharField(max_length=32, blank=True, unique=True)
    value = encrypt(models.TextField(default=None, blank=True, null=True))
