import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from storage.filesystem import File, FileSystemStorage


class FileTestCase(TestCase):
    def test_content_type(self):
        file = File((settings.TEST_RESOURCES_DIR / "artifacts/artifact-aa.zip").open("rb"))
        assert file.content_type == "application/zip"


class FileSystemStorageTestCase(TestCase):
    def setUp(self):
        # Create a temporary directory for the test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = FileSystemStorage(location=self.temp_dir.name)

    def tearDown(self):
        # Delete the temporary directory and its contents
        self.temp_dir.cleanup()

    def test_file_upload(self):
        # Create a temporary file with some data
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(b"Hello, world!")
            f.flush()
            path = Path(f.name)

            # Upload the file to the storage backend
            with self.storage.open("test.txt", "wb") as destination:
                with path.open("rb") as source:
                    destination.write(source.read())

            # Check that the file was uploaded correctly
            assert self.storage.exists("test.txt")
            assert self.storage.size("test.txt") == path.stat().st_size

    def test_file_download(self):
        # Create a temporary file with some data
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(b"Hello, world!")
            f.flush()
            path = Path(f.name)

            # Upload the file to the storage backend
            with self.storage.open("test.txt", "wb") as destination:
                with path.open("rb") as source:
                    destination.write(source.read())

            # Download the file from the storage backend
            with self.storage.open("test.txt", "rb") as source:
                data = source.read()

            # Check that the downloaded data is correct
            assert data == b"Hello, world!"

    def test_file_delete(self):
        # Create a temporary file with some data
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(b"Hello, world!")
            f.flush()
            path = Path(f.name)

            # Upload the file to the storage backend
            with self.storage.open("test.txt", "wb") as destination:
                with path.open("rb") as source:
                    destination.write(source.read())

            assert self.storage.exists("test.txt")

            # Delete the file from the storage backend
            self.storage.delete("test.txt")

            # Check that the file was deleted
            assert not self.storage.exists("test.txt")
