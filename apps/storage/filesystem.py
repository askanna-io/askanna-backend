from pathlib import Path

from django.core.files.storage import FileSystemStorage as DjangoFileSystemStorage
from django.utils.deconstruct import deconstructible

from storage.file import File


@deconstructible(path="storage.filesystem.FileSystemStorage")
class FileSystemStorage(DjangoFileSystemStorage):
    file_class = File
    support_chunks = True

    def _open(self, name: str, mode="rb"):
        return self.file_class(Path(self.path(name)).open(mode))
