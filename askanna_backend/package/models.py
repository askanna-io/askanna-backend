import os
import uuid

from core.models import AuthorModel, BaseModel
from django.conf import settings
from django.db import models


class Package(AuthorModel, BaseModel):
    original_filename = models.CharField(max_length=1000, default="")

    project = models.ForeignKey(
        "project.Project",
        on_delete=models.CASCADE,
        related_name="packages",
        related_query_name="package",
        null=True,
        blank=True,
        default=None,
    )
    size = models.IntegerField(help_text="Size of this package in bytes")

    @property
    def storage_location(self):
        return os.path.join(self.project.uuid.hex, self.uuid.hex,)

    @property
    def stored_path(self):
        return os.path.join(
            settings.PACKAGES_ROOT, self.storage_location, self.filename
        )

    @property
    def filename(self):
        return "package_{}.zip".format(self.uuid.hex)

    @property
    def read(self):
        """
            Read the package from filesytem
        """
        with open(self.stored_path, "rb") as f:
            return f.read()

    def prune(self):
        """
        Delete the files and metadata linked to this instance
        """
        os.remove(self.stored_path)

    class Meta:
        ordering = ["-created"]


class ChunkedPackagePart(models.Model):
    uuid = models.UUIDField(
        primary_key=True, db_index=True, editable=False, default=uuid.uuid4
    )
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this chunk of the package")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    package = models.ForeignKey(
        Package, on_delete=models.CASCADE, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]
