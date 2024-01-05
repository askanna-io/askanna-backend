import uuid as _uuid
from pathlib import Path

from django.db import models
from django.utils import timezone

from core.fields import CreationDateTimeField, ModificationDateTimeField
from core.utils.suuid import create_suuid


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
    suuid = models.CharField(max_length=32, default=create_suuid, unique=True, editable=False, verbose_name="SUUID")

    created_at = CreationDateTimeField()
    modified_at = ModificationDateTimeField()

    deleted_at = models.DateTimeField(blank=True, auto_now_add=False, auto_now=False, null=True)

    class Meta:
        abstract = True
        get_latest_by = "modified_at"
        ordering = ["-modified_at"]

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

    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=False, default="")

    class Meta:
        abstract = True

    def __str__(self):
        if self.name:
            return f"{self.__class__.__name__}: {self.name} ({self.suuid})"
        return f"{self.__class__.__name__} object ({self.suuid})"


class AuthorModel(models.Model):
    """
    Adding created_by to the model to register who created this instance
    """

    created_by_user = models.ForeignKey("account.User", on_delete=models.SET_NULL, blank=True, null=True)
    created_by_member = models.ForeignKey("account.Membership", on_delete=models.CASCADE, null=True)

    class Meta:
        abstract = True


class FileBaseModel(BaseModel):
    """
    Providing basic accessors to a file on the filesystem related to a model
    """

    file_type = "file"
    file_extension = ""
    file_readmode = "r"
    file_writemode = "w"

    class Meta:
        abstract = True
        get_latest_by = "modified_at"
        ordering = ["-modified_at"]

    @property
    def filename(self) -> str:
        base_filename = f"{self.file_type}_{self.uuid.hex}"

        if self.file_extension:
            return f"{base_filename}.{self.file_extension}"

        return base_filename

    @property
    def storage_location(self) -> Path:
        return self.get_storage_location()

    @property
    def root_storage_location(self) -> Path:
        return self.get_root_location() / self.storage_location

    @property
    def stored_path(self) -> Path:
        return self.root_storage_location / self.filename

    def get_storage_location(self) -> Path:
        raise NotImplementedError(f"Please implement 'get_storage_location' for {self.__class__.__name__}")

    def get_root_location(self) -> Path:
        raise NotImplementedError(f"Please implement 'get_root_location' for {self.__class__.__name__}")

    @property
    def read(self):
        return self.stored_path.open(mode=self.file_readmode).read()

    def write(self, stream):
        """
        Write contents to the filesystem
        """
        Path.mkdir(self.root_storage_location, parents=True, exist_ok=True)
        self.stored_path.open(self.file_writemode).write(stream.read())

    def prune(self):
        Path.unlink(self.stored_path, missing_ok=True)

        try:
            Path.rmdir(self.root_storage_location)
        # If the directory is not empty or does not exist, we don't want to remove it
        except (FileNotFoundError, OSError):
            pass


class VisibilityModel(models.Model):
    VISIBLITY = (
        ("PRIVATE", "PRIVATE"),
        ("PUBLIC", "PUBLIC"),
    )

    DEFAULT_VISIBILITY = "PRIVATE"

    visibility = models.CharField(max_length=10, choices=VISIBLITY, default=DEFAULT_VISIBILITY, db_index=True)

    class Meta:
        abstract = True

    @property
    def is_private(self) -> bool:
        return self.visibility == "PRIVATE"

    @property
    def is_public(self) -> bool:
        return self.visibility == "PUBLIC"
