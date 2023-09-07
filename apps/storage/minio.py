"""
For the MinIO Storage found inspiration in the following project:
- django-minio-storage: https://github.com/py-pa/django-minio-storage/
- django-minio-backend: https://github.com/theriverman/django-minio-backend
- django-storages: https://github.com/jschneier/django-storages/
"""
import logging
import mimetypes
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from tempfile import SpooledTemporaryFile

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from minio import Minio
from minio.datatypes import Object as MinioObject
from minio.error import S3Error
from urllib3.response import HTTPResponse

from core.utils.config import get_setting

logger = logging.getLogger(__name__)
MinioSettings = namedtuple(
    "MinioSettings",
    [
        "endpoint",
        "use_https",
        "external_endpoint",
        "external_use_https",
        "access_key",
        "secret_key",
        "default_bucket_name",
    ],
)


class MinioFile(File):
    """A Django File class which buffers the MinIO object into a local SpooledTemporaryFile."""

    max_memory_size: int = 10 * 1024 * 1024

    def __init__(self, name: str, mode: str, storage: "MinioStorage"):
        self.name: str = name
        self.mode: str = mode

        self._storage: MinioStorage = storage
        self._file = None

    @property
    def file(self):
        if self._file is None:
            minio_object = None
            try:
                minio_object = self._storage.get_object(self.name)
                self._file = SpooledTemporaryFile(max_size=self.max_memory_size)
                for chunk in minio_object.stream(amt=1024 * 1024):
                    self._file.write(chunk)
                self._file.seek(0)
            finally:
                if minio_object:
                    minio_object.close()
                    minio_object.release_conn()

        return self._file

    def read(self, *args, **kwargs):
        if "r" not in self.mode:
            raise AttributeError("File was not opened in read mode.")
        return super().read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        if "r" not in self.mode:
            raise AttributeError("File was not opened in read mode.")
        return super().readline(*args, **kwargs)

    def write(self, content):
        raise NotImplementedError(f"{__class__} doesn't support write")

    @cached_property
    def size(self) -> int:
        return self._storage.size(self.name)

    @cached_property
    def content_type(self) -> str:
        return self._storage.get_content_type(self.name)

    @cached_property
    def last_modified(self) -> datetime:
        return self._storage.get_modified_time(self.name)

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None


@deconstructible(path="storage.minio.MinioStorage")
class MinioStorage(Storage):
    """A Django Storage class for the MinIO object storage using the MinIO Python Client."""

    file_class = MinioFile
    default_content_type = settings.ASKANNA_DEFAULT_CONTENT_TYPE
    default_bucket_name = "askanna"

    def __init__(self, bucket_name: str | None = None):
        self._client_internal = None
        self._client_external = None
        self._settings = None
        self._bucket_name = bucket_name

    @property
    def settings(self) -> MinioSettings:
        if self._settings is None:
            minio_settings = get_setting("MINIO_SETTINGS", dict)

            self._settings = MinioSettings(
                endpoint=minio_settings.get("ENDPOINT", None),
                use_https=minio_settings.get("USE_HTTPS", False),
                external_endpoint=minio_settings.get("EXTERNAL_ENDPOINT", None),
                external_use_https=minio_settings.get("EXTERNAL_USE_HTTPS", False),
                access_key=minio_settings.get("ACCESS_KEY", None),
                secret_key=minio_settings.get("SECRET_KEY", None),
                default_bucket_name=minio_settings.get("DEFAULT_BUCKET_NAME", self.default_bucket_name),
            )

        return self._settings

    @property
    def bucket_name(self) -> str:
        if self._bucket_name is None:
            self._bucket_name = self.settings.default_bucket_name

        return self._bucket_name

    @property
    def client_internal(self) -> Minio:
        """Get or create a Minio client instance"""
        if self._client_internal is None:
            self._client_internal = Minio(
                endpoint=self.settings.endpoint,
                secure=self.settings.use_https,
                access_key=self.settings.access_key,
                secret_key=self.settings.secret_key,
            )

        return self._client_internal

    @property
    def client_external(self) -> Minio:
        """Get or create a Minio client instance for the base url"""
        if self._client_external is None:
            external_endpoint = self.settings.external_endpoint

            if external_endpoint:
                self._client_external = Minio(
                    endpoint=external_endpoint,
                    secure=self.settings.external_use_https,
                    http_client=self.client_internal._http,
                    region=self.client_internal._get_region(self.bucket_name, None),
                    credentials=self.client_internal._provider,
                )
            else:
                self._client_external = self.client_internal

        return self._client_external

    def _normalize_name(self, name: str) -> str:
        posix_name = Path(name).as_posix().replace("\\", "/")

        if name.endswith("/") and not posix_name.endswith("/"):
            return posix_name + "/"

        return posix_name

    def _open(self, name: str, mode="rb"):
        return self.file_class(self._normalize_name(name), mode, self)

    def _save(self, name: str, content: InMemoryUploadedFile) -> str:
        object_name = self._normalize_name(name)

        if hasattr(content, "seek") and callable(content.seek):
            content.seek(0)

        if not self.client_internal.bucket_exists(self.bucket_name):
            self.client_internal.make_bucket(self.bucket_name)

        response = self.client_internal.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=content,
            length=content.size,
            content_type=getattr(
                content, "content_type", mimetypes.guess_type(object_name)[0] or self.default_content_type
            ),
        )

        return response.object_name

    def delete(self, name: str):
        """Deletes the file referenced by name from the storage system."""
        self.client_internal.remove_object(self.bucket_name, self._normalize_name(name))

    def get_object(self, name: str) -> HTTPResponse:
        """Get a MinIO object of a file referenced by name.

        Do not forget to close the object after using it and to release the connection.
        """
        return self.client_internal.get_object(self.bucket_name, object_name=self._normalize_name(name))

    def get_stat_object(self, name: str) -> MinioObject:
        """Get object information and metadata of a MinIO object"""
        return self.client_internal.stat_object(self.bucket_name, object_name=self._normalize_name(name))

    def exists(self, name: str) -> bool:
        """Returns True if a file referenced by name exists in the storage system, or False if it does not exists."""
        try:
            if self.get_stat_object(name):
                return True
            return False
        except S3Error as exc:
            if "does not exist" in exc.message:
                return False
            raise exc

    def listdir(self, path: str | None = None) -> tuple[list[str], list[str]]:
        """Lists the contents of the bucket on the specified path. If the path is not specified, the contents of the
        root of the bucket is returned.

        listdir returns a 2-tuple of lists; the first item being directories, the second item being files.
        """

        if path:
            if not path.endswith("/"):
                path += "/"
            path = self._normalize_name(path)

        minio_objects = self.client_internal.list_objects(bucket_name=self.bucket_name, prefix=path, recursive=False)

        dirs = set()
        files = set()
        for minio_object in minio_objects:
            # If path is not None, remove path from object name
            object_name = minio_object.object_name[len(path) :] if path else minio_object.object_name

            if object_name.endswith("/"):
                dirs.add(object_name[:-1])
            else:
                files.add(object_name)

        return list(dirs), list(files)

    def size(self, name: str) -> int:
        """Returns the total size, in bytes, of a file referenced by name."""
        return self.get_stat_object(name).size or 0

    def url(self, name: str) -> str:
        """Returns the URL where the contents of a file referenced by name can be accessed."""
        return self.client_external.presigned_get_object(self.bucket_name, self._normalize_name(name))

    def path(self, name):
        """MinIO Storage doesn't support path"""
        raise NotImplementedError("MinIO does not support path")

    def get_content_type(self, name: str) -> str:
        """Returns the content type of a file referenced by name."""
        return self.get_stat_object(name).content_type or self.default_content_type

    def get_accessed_time(self, name: str):
        """MinIO does not store last accessed time"""
        raise NotImplementedError("MinIO does not store last accessed time")

    def get_created_time(self, name: str):
        """MinIO does not store creation time"""
        raise NotImplementedError("MinIO does not store creation time")

    def get_modified_time(self, name: str) -> datetime:
        """
        Return the last modified time (as a datetime) of a file referenced by name. The datetime will be
        timezone-aware if USE_TZ=True.
        """
        last_modified = self.get_stat_object(name).last_modified

        if not last_modified or type(last_modified) != datetime:
            raise OSError(f"Could not access modified time for file '{name}' on bucket '{self.bucket_name}'")

        if get_setting("USE_TZ"):
            return last_modified

        return last_modified.replace(tzinfo=None)
