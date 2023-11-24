from pathlib import Path
from tempfile import SpooledTemporaryFile
from zipfile import ZipFile

from django.conf import settings
from django.core.files.storage import storages
from django.db import models
from django.utils.functional import cached_property

from core.models import NameDescriptionBaseModel, ObjectReference
from core.permissions.askanna import AskAnnaPermissionByAction


def get_upload_file_to(instance, filename):
    if instance.upload_to is None:
        return f"uploads/{filename}"

    return f"{instance.upload_to}/{filename}"


class FileQuerySet(models.QuerySet):
    def active(self, add_select_related=False):
        active_query = self.filter(
            deleted_at__isnull=True,
            _created_for__account_user__deleted_at__isnull=True,
            _created_for__account_membership__deleted_at__isnull=True,
            _created_for__package_package__deleted_at__isnull=True,
        ).select_related(
            "_created_for__account_user",
            "_created_for__account_membership__user",
            "_created_for__package_package__project__workspace__created_by_user",
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
    size = models.IntegerField(null=True, help_text="Size of the file in bytes")
    etag = models.CharField(blank=True, max_length=255, help_text="MD5 digest of the file")
    content_type = models.CharField(blank=True, max_length=255, help_text="Content type of the file")

    completed_at = models.DateTimeField(
        null=True, default=None, help_text="Date and time when upload of this file was finished"
    )

    _created_for = models.ForeignKey(
        ObjectReference, on_delete=models.CASCADE, related_name="file_created_for", db_column="created_for"
    )
    _created_by = models.ForeignKey(
        ObjectReference, on_delete=models.CASCADE, related_name="file_created_by", db_column="created_by"
    )

    # We use the property upload_to to have the option to dynamically set the upload_to path when uploading a file
    _upload_to = None

    _part_filenames = None

    objects = FileManager.from_queryset(FileQuerySet)()

    def __str__(self):
        return f"{self.name or self.file.name} ({self.suuid})"

    @property
    def upload_to(self):
        if not self._upload_to:
            self._upload_to = self.created_for.upload_directory
        return self._upload_to

    @upload_to.setter
    def upload_to(self, value):
        self._upload_to = value

    @property
    def storage(self):
        return storages["default"]

    @property
    def created_for(self):
        return self._created_for.object

    @property
    def created_by(self):
        return self._created_by.object

    def get_upload_to_part_name(self, part_number: int) -> str:
        filename = f"{self.suuid}_part_{str(part_number).zfill(5)}.part"
        return self.upload_to + "/" + filename

    @cached_property
    def is_zipfile(self) -> bool:
        if self.file is None or self.completed_at is None:
            return False
        return self.content_type == "application/zip"

    @cached_property
    def zipfile_namelist(self) -> list[str]:
        if not self.is_zipfile:
            raise ValueError("File is not a Zipfile")

        with self.file.open() as zip_file:
            return ZipFile(zip_file).namelist()

    def get_file_from_zipfile(self, file_path: str) -> SpooledTemporaryFile:
        if not self.is_zipfile:
            raise ValueError("File is not a Zipfile")

        if file_path not in self.zipfile_namelist:
            raise FileNotFoundError(f"File {file_path} not found in zipfile")

        with self.file.open() as zip_file, ZipFile(zip_file).open(file_path) as file_in_zip:
            file = SpooledTemporaryFile(
                max_size=settings.FILE_MAX_MEMORY_SIZE,
                suffix=".FileInZipfile",
            )
            file.write(file_in_zip.read())
            file.seek(0)

        return file

    @property
    def part_filenames(self) -> list[str]:
        if not self._part_filenames:
            if settings.ASKANNA_FILESTORAGE == "filesystem" and not self.storage.exists(self.upload_to):
                return []

            filenames = sorted(self.storage.listdir(self.upload_to)[1])
            self._part_filenames = [
                filename
                for filename in filenames
                if filename.startswith(f"{self.suuid}_part_") and filename.endswith(".part")
            ]

        return self._part_filenames

    def delete_parts(self):
        for file in self.part_filenames:
            self.storage.delete(self.upload_to + "/" + file)
        self._part_filenames = None

    def delete_file_and_empty_directories(self):
        if not self.file and not self.part_filenames:
            return

        if settings.ASKANNA_FILESTORAGE != "filesystem":
            directories = None
        elif self.file:
            directories = Path(self.file.path).parents
        else:
            directories = Path(self.storage.path(self.upload_to) + "/" + self.part_filenames[0]).parents

        if self.part_filenames:
            self.delete_parts()
        if self.file:
            self.file.delete(save=False)

        if directories:
            for directory in directories:
                if (
                    directory.exists()
                    and directory.is_dir()
                    and not any(directory.iterdir())  # Only delete empty directories
                    and directory != settings.STORAGE_ROOT  # Don't delete the storage root directory
                ):
                    directory.rmdir()
                else:
                    break

    def request_has_object_read_permission(self, request, view) -> bool:
        return AskAnnaPermissionByAction().has_object_permission(request, view, self.created_for)

    def request_has_object_write_permission(self, request, view) -> bool:
        return AskAnnaPermissionByAction().has_object_permission(request, view, self.created_for)
