from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.test import override_settings

from storage.utils.file import (
    get_content_type_from_file,
    get_md5_from_file,
    is_json_file,
)


class TestGetContentTypeFromFile:
    def test_get_content_type_from_file(self, avatar_file):
        content_type = get_content_type_from_file(avatar_file)
        assert content_type == "image/jpeg"

    def test_get_content_type_from_yml_file(self):
        test_file = settings.TEST_RESOURCES_DIR / "askannaconfig.yml"
        content_type = get_content_type_from_file(test_file)
        assert content_type == "text/plain"

    def test_get_content_type_from_zipfile(self, mixed_format_zipfile):
        content_type = get_content_type_from_file(mixed_format_zipfile["file"])
        assert content_type == "application/zip"

    def test_get_content_type_from_contentfile(self, mixed_format_zipfile):
        content_file = ContentFile(mixed_format_zipfile["file"].read_bytes(), name="test.zip")
        content_type = get_content_type_from_file(content_file)
        assert content_type == "application/zip"

    def test_zip(self):
        filepath = settings.TEST_RESOURCES_DIR / "artifacts" / "artifact-aa.zip"
        assert get_content_type_from_file(filepath) == "application/zip"

    def test_json(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.json"
        assert get_content_type_from_file(filepath) == "application/json"

    def test_txt(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.txt"
        assert get_content_type_from_file(filepath) == "text/plain"

    def test_json_file_unknown(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload-json.txt"
        assert get_content_type_from_file(filepath) == "application/json"

    def test_python(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "python.py"
        # not all platforms return the same mimetype, so we match on 2 different
        assert get_content_type_from_file(filepath) == "text/x-script.python"

    def test_file_not_found(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "does-not-exist.txt"
        with pytest.raises(FileNotFoundError):
            get_content_type_from_file(filepath)

    def test_get_content_type_from_file_use_mimetypes(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "python.py"

        with patch("magic.from_buffer", return_value=None), patch("magic.from_file", return_value=None):
            content_type = get_content_type_from_file(filepath)

        assert content_type == "text/x-python"


class TestGetMD5FromFile:
    @pytest.fixture(autouse=True)
    def _set_fixtures(self):
        self.test_file = settings.TEST_RESOURCES_DIR / "askannaconfig.yml"

    def test_get_md5_from_file(self):
        md5 = get_md5_from_file(self.test_file)
        assert md5 == "adb769e6f5604bf5a9b6c9c193701389"

    def test_get_md5_from_contentfile(self):
        test_file = ContentFile(self.test_file.read_bytes())
        md5 = get_md5_from_file(test_file)
        assert md5 == "adb769e6f5604bf5a9b6c9c193701389"

    @override_settings(FILE_MAX_MEMORY_SIZE=5)
    def test_get_md5_from_contentfile_chunks(self):
        test_file = ContentFile(self.test_file.read_bytes())
        md5 = get_md5_from_file(test_file)
        assert md5 == "adb769e6f5604bf5a9b6c9c193701389"


class TestIsJsonFile:
    def test_json(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.json"
        assert is_json_file(filepath)

    def test_json_file_unknown(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload-json.txt"
        assert is_json_file(filepath)

    def test_txt(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.txt"
        assert not is_json_file(filepath)

    def test_file_not_found(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "does-not-exist.txt"
        with pytest.raises(FileNotFoundError):
            is_json_file(filepath)
