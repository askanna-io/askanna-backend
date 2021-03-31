# -*- coding: utf-8 -*-
import unittest

from django.conf import settings
from core.utils import detect_file_mimetype


class TestFiletype(unittest.TestCase):
    def test_zip(self):
        filepath = str(settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip"))
        self.assertEqual("application/zip", detect_file_mimetype(filepath))

    def test_json(self):
        filepath = str(settings.TEST_RESOURCES_DIR.path("payloads/test-payload.json"))
        self.assertEqual("application/json", detect_file_mimetype(filepath))

    def test_txt(self):
        filepath = str(settings.TEST_RESOURCES_DIR.path("payloads/test-payload.txt"))
        self.assertEqual("text/plain", detect_file_mimetype(filepath))

    def test_python(self):
        filepath = str(settings.TEST_RESOURCES_DIR.path("misc/python.py"))

        # not all platforms return the same mimetype, so we match on 2 different
        self.assertIn(
            detect_file_mimetype(filepath), ["text/x-script.python", "text/x-python"]
        )
