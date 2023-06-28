import unittest

from django.conf import settings

from core.utils import detect_file_mimetype, is_jsonfile


class TestDetectFileMimetype(unittest.TestCase):
    def test_zip(self):
        filepath = settings.TEST_RESOURCES_DIR / "artifacts" / "artifact-aa.zip"
        assert detect_file_mimetype(filepath) == "application/zip"

    def test_json(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.json"
        assert detect_file_mimetype(filepath) == "application/json"

    def test_txt(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.txt"
        assert detect_file_mimetype(filepath) == "text/plain"

    def test_json_file_unknown(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload-json.txt"
        assert detect_file_mimetype(filepath) == "application/json"

    def test_python(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "python.py"
        # not all platforms return the same mimetype, so we match on 2 different
        assert detect_file_mimetype(filepath) in ["text/x-script.python", "text/x-python"]

    def test_file_not_found(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "does-not-exist.txt"
        with self.assertRaises(FileNotFoundError):
            detect_file_mimetype(filepath)


class TestIsJsonFile(unittest.TestCase):
    def test_json(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.json"
        assert is_jsonfile(filepath)

    def test_json_file_unknown(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload-json.txt"
        assert is_jsonfile(filepath)

    def test_txt(self):
        filepath = settings.TEST_RESOURCES_DIR / "payloads" / "test-payload.txt"
        assert not is_jsonfile(filepath)

    def test_file_not_found(self):
        filepath = settings.TEST_RESOURCES_DIR / "misc" / "does-not-exist.txt"
        with self.assertRaises(FileNotFoundError):
            is_jsonfile(filepath)
