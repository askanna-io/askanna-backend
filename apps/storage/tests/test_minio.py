import datetime
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from minio.error import S3Error

from core.utils.config import get_setting
from storage.minio import MinioSettings, MinioStorage

pytestmark = pytest.mark.django_db


@override_settings(MINIO_DEFAULT_BUCKET_NAME="askanna-test")
class TestMinio(TestCase):
    def setUp(self):
        self.storage = MinioStorage()
        self.file = self.storage.save("test-file.txt", ContentFile(b"test"))

        self.storage_custom_bucket = MinioStorage(bucket_name="askanna-test-custom")
        self.file_custom_bucket = self.storage_custom_bucket.save("test-file.txt", ContentFile(b"testing"))

    def tearDown(self):
        objects = self.storage.client_internal.list_objects(self.storage.bucket_name, recursive=True)
        for object in objects:
            self.storage.client_internal.remove_object(self.storage.bucket_name, object.object_name)

        objects = self.storage_custom_bucket.client_internal.list_objects(
            self.storage_custom_bucket.bucket_name, recursive=True
        )
        for object in objects:
            self.storage_custom_bucket.client_internal.remove_object(
                self.storage_custom_bucket.bucket_name, object.object_name
            )
        self.storage_custom_bucket.client_internal.remove_bucket(self.storage_custom_bucket.bucket_name)

    def test_open_file(self):
        file = self.storage.open(self.file)
        assert file.read() == b"test"

    def test_open_custom_bucket(self):
        file = self.storage_custom_bucket.open(self.file_custom_bucket)
        assert file.read() == b"testing"

    def test_file_save(self):
        assert not self.storage.exists("trivial.txt")

        test_file = self.storage.save("trivial.txt", ContentFile(b"12345"))
        assert test_file == "trivial.txt"
        assert self.storage.exists("trivial.txt")

        self.storage.client_internal.remove_object(self.storage.bucket_name, test_file)

    def test_file_save_to_custom_bucket(self):
        assert not self.storage_custom_bucket.exists("trivial_custom.txt")

        test_file = self.storage_custom_bucket.save("trivial_custom.txt", ContentFile(b"abcdef"))
        assert test_file == "trivial_custom.txt"
        assert self.storage_custom_bucket.exists("trivial_custom.txt")

        self.storage_custom_bucket.client_internal.remove_object(self.storage_custom_bucket.bucket_name, test_file)

    def test_file_read(self):
        file = self.storage.open(self.file)
        assert file.read() == b"test"

    def test_file_readline(self):
        file = self.storage.open(self.file)
        assert file.readline() == b"test"

    def test_file_delete(self):
        assert not self.storage.exists("trivial_delete.txt")

        self.storage.save("trivial_delete.txt", ContentFile(b"12345"))
        assert self.storage.exists("trivial_delete.txt")

        self.storage.delete("trivial_delete.txt")
        assert not self.storage.exists("trivial_delete.txt")

    def test_file_exists(self):
        assert self.storage.exists(self.file)
        assert not self.storage.exists("not-existing-file")

    def test_listdir(self):
        result = self.storage.listdir()
        assert result == ([], ["test-file.txt"])

        self.storage.save("in-path/test-file-2.txt", ContentFile(b"test"))
        result = self.storage.listdir()
        assert result == (["in-path"], ["test-file.txt"])

        result = self.storage.listdir("in-path")
        assert result == ([], ["test-file-2.txt"])

    def test_file_size(self):
        assert self.storage.size(self.file) == 4

        file = self.storage.open(self.file)
        assert file.size == 4

    def test_content_type(self):
        assert self.storage.get_content_type(self.file) == "text/plain"

        file = self.storage.open(self.file)
        assert file.content_type == "text/plain"

    def test_last_modified(self):
        assert self.storage.get_modified_time(self.file) is not None
        assert isinstance(self.storage.get_modified_time(self.file), datetime.datetime)

        file = self.storage.open(self.file)
        assert file.last_modified is not None
        assert isinstance(file.last_modified, datetime.datetime)

    def test_url(self):
        assert self.storage.url(self.file).startswith(
            f"http://localhost:9000/{self.storage.bucket_name}/{self.file}?X-Amz-Algorithm="
        )

    def test_url_without_external_endpoint(self):
        minio_settings = get_setting("MINIO_SETTINGS", dict)
        settings = MinioSettings(
            endpoint=minio_settings.get("ENDPOINT", None),
            use_https=minio_settings.get("USE_HTTPS", False),
            external_endpoint=None,
            external_use_https=False,
            access_key=minio_settings.get("ACCESS_KEY", None),
            secret_key=minio_settings.get("SECRET_KEY", None),
            default_bucket_name=minio_settings.get("DEFAULT_BUCKET_NAME", "askanna"),
        )
        self.storage._settings = settings

        assert self.storage.url(self.file).startswith(
            f"http://minio:9000/{self.storage.bucket_name}/{self.file}?X-Amz-Algorithm="
        )

    @patch("storage.minio.MinioStorage.get_stat_object", return_value=None)
    def test_file_empty_stat_object(self, mock_get_stat_object):
        assert self.storage.exists(self.file) is False

    @patch(
        "storage.minio.MinioStorage.get_stat_object",
        side_effect=S3Error("test", "Object does not exist", "test", "test", "test", "test"),
    )
    def test_file_s3_error_not_exist(self, mock_get_stat_object):
        assert self.storage.exists(self.file) is False

    @patch(
        "storage.minio.MinioStorage.get_stat_object",
        side_effect=S3Error("test", "test", "test", "test", "test", "test"),
    )
    def test_file_s3_error_other_then_not_exist(self, mock_get_stat_object):
        with pytest.raises(S3Error) as exc:
            assert self.storage.exists(self.file)
            assert exc.code == "test"  # type: ignore
