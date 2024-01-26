import uuid as _uuid

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
