import os
import uuid
from typing import Union

from core.config import AskAnnaConfig
from core.models import AuthorModel, NameDescriptionBaseModel
from django.conf import settings
from django.db import models
from django.db.models import Q
from package.signals import package_upload_finish


class PackageQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted_at__isnull=True,
            project__deleted_at__isnull=True,
            project__workspace__deleted_at__isnull=True,
        ).exclude(original_filename="")

    def active_and_finished(self):
        return self.active().filter(finished_at__isnull=False)

    def inactive(self):
        return self.filter(
            Q(deleted_at__isnull=False)
            | Q(project__deleted_at__isnull=False)
            | Q(project__workspace__deleted_at__isnull=False)
        )


class PackageManager(models.Manager):
    def get_queryset(self):
        return PackageQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def active_and_finished(self):
        return self.get_queryset().active_and_finished()

    def inactive(self):
        return self.get_queryset().inactive()


class Package(AuthorModel, NameDescriptionBaseModel):
    original_filename = models.CharField(max_length=1000, default="")

    project = models.ForeignKey(
        "project.Project",
        on_delete=models.CASCADE,
        related_name="packages",
        null=True,
        blank=True,
        default=None,
    )
    size = models.IntegerField(help_text="Size of this package in bytes")

    member = models.ForeignKey("account.Membership", on_delete=models.CASCADE, null=True)

    # Store when it was finished uploading
    finished_at = models.DateTimeField(
        "Finished upload at",
        blank=True,
        auto_now_add=False,
        auto_now=False,
        null=True,
        help_text="Date and time when upload of this package was finished",
        db_index=True,
    )

    objects = PackageManager()

    def __str__(self):
        if self.original_filename:
            return f"{self.original_filename} ({self.suuid})"
        return self.suuid

    @property
    def storage_location(self):
        return os.path.join(
            self.project.uuid.hex,
            self.uuid.hex,
        )

    @property
    def stored_path(self):
        return os.path.join(settings.PACKAGES_ROOT, self.storage_location, self.filename)

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

    def write(self, stream):
        """
        Write contents to the filesystem
        """
        os.makedirs(os.path.join(settings.PACKAGES_ROOT, self.storage_location), exist_ok=True)
        with open(self.stored_path, "wb") as f:
            f.write(stream.read())

        # unpack the package via signal
        package_upload_finish.send(
            sender=self.__class__,
            postheaders={},
            obj=self,
        )

    def prune(self):
        """
        Delete the files and metadata linked to this instance
        """
        if os.path.exists(self.stored_path):
            os.remove(self.stored_path)

    def get_askanna_yml_path(self) -> Union[str, None]:
        """
        Read the askanna.yml from the package stored on the settings.BLOB_ROOT
        If file doesn't exist, return None
        """
        package_path = os.path.join(settings.BLOB_ROOT, str(self.uuid))

        # read config from askanna.yml
        askanna_yml_path = os.path.join(package_path, "askanna.yml")
        if not os.path.exists(askanna_yml_path):
            return None
        return askanna_yml_path

    def get_askanna_config(self) -> Union[AskAnnaConfig, None]:
        """
        Reads the askanna.yml as is and return as AskAnnaConfig or None
        """
        askanna_yml = self.get_askanna_yml_path()
        if not askanna_yml:
            return None
        return AskAnnaConfig.from_stream(open(askanna_yml, "r"))

    class Meta:
        ordering = ["-created_at"]


class ChunkedPackagePart(models.Model):
    uuid = models.UUIDField(primary_key=True, db_index=True, editable=False, default=uuid.uuid4)
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this chunk of the package")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    package = models.ForeignKey(Package, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]
