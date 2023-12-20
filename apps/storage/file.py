from pathlib import Path

from django.conf import settings
from django.core.files import File as DjangoFile
from django.utils.functional import cached_property

from storage.utils.file import get_content_type_from_file


class File(DjangoFile):
    default_content_type = settings.ASKANNA_DEFAULT_CONTENT_TYPE

    @cached_property
    def content_type(self) -> str:
        return get_content_type_from_file(Path(self.name), default=self.default_content_type)


class MultipartFile(File):
    def __init__(
        self, file, name: str = None, storage=None, part_filenames: list[str] = None, directory: Path | str = None
    ):
        self.file = file

        if name is None:
            name = getattr(file, "name", None)
        self.name = name

        if storage is None:
            storage = getattr(file, "storage", None)
        self.storage = storage
        assert self.storage is not None

        if part_filenames is None and hasattr(file, "instance"):
            part_filenames = getattr(file.instance, "part_filenames", None)
        self.part_filenames = part_filenames
        assert self.part_filenames is not None

        if directory is None and hasattr(file, "instance"):
            directory = getattr(file.instance, "upload_to", None)
        self.directory = directory
        assert self.directory is not None

        self.mode = file.mode if hasattr(file, "mode") else "rb"

    @cached_property
    def size(self) -> int:
        size = 0
        for part_filename in self.part_filenames:
            part_file = self.directory + "/" + part_filename
            with self.storage.open(part_file) as f:
                size += f.size

        return size

    def chunks(self):
        for part_filename in self.part_filenames:
            part_file = self.directory + "/" + part_filename
            with self.storage.open(part_file) as f:
                yield f.read()
