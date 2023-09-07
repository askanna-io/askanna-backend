from pathlib import Path

from django.conf import settings
from django.core.files import File as DjangoFile
from django.core.files.storage import FileSystemStorage as DjangoFileSystemStorage
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property

from core.utils import detect_file_mimetype


class File(DjangoFile):
    default_content_type = settings.ASKANNA_DEFAULT_CONTENT_TYPE

    @cached_property
    def content_type(self) -> str:
        return detect_file_mimetype(Path(self.name)) or self.default_content_type


@deconstructible(path="storage.filesystem.FileSystemStorage")
class FileSystemStorage(DjangoFileSystemStorage):
    file_class = File

    def _open(self, name: str, mode="rb"):
        return self.file_class(Path(self.path(name)).open(mode))
