# -*- coding: utf-8 -*-
import unittest

from django.conf import settings
import pytest

from core.config import AskAnnaConfig
from core.utils import get_config, get_config_from_string, get_setting_from_database

pytestmark = pytest.mark.django_db


class TestConfigLoader(unittest.TestCase):
    def test_load_config_from_file(self):
        """
        Here we just test loading the config from a file, not judging on whether it is valid or not
        """
        filename = settings.TEST_RESOURCES_DIR.path("projects/project-001/askanna.yml")
        self.assertEqual(
            get_config(filename),
            {
                "a-non-job": "some random string",
                "my-second-test-job": {
                    "environment": {"image": "python:3-slim"},
                    "job": ["python my_script.py"],
                    "schedule": [
                        "0 12 * * *",
                        {"day": 5, "hour": 5, "month": 5},
                        {"century": 2, "hour": 8},
                        "some rubbish, no cron",
                    ],
                },
                "my-test-job": {
                    "job": ["python my_script.py"],
                    "notifications": {"all": {"email": ["anna@askanna.io"]}},
                },
            },
        )

    def test_load_config_from_string(self):
        askanna_yml = """
---
my-test-job:
  job:
    - python my_script.py

        """
        self.assertEqual(
            get_config_from_string(askanna_yml),
            {"my-test-job": {"job": ["python my_script.py"]}},
        )

    def test_load_config_from_string_emptyconfig(self):
        askanna_yml = """

        """
        self.assertEqual(
            get_config_from_string(askanna_yml),
            None,
        )

    def test_load_config_from_string_errorconfig(self):
        askanna_yml = """
asimov:
  - "" > test {}
        """
        self.assertEqual(
            get_config_from_string(askanna_yml),
            None,
        )


class TestDatabaseSetting(unittest.TestCase):
    def test_get_setting_from_db(self):
        self.assertEqual(get_setting_from_database("some-setting"), None)
        self.assertEqual(get_setting_from_database("some-setting", False), False)
        self.assertEqual(get_setting_from_database("some-setting", True), True)


class TestAskAnnaConfig(unittest.TestCase):
    def test_notifications_global(self):
        yml = settings.TEST_RESOURCES_DIR.path("askannaconfig.yml")
        config = AskAnnaConfig.from_stream(open(yml, "r"))

        self.assertEqual(
            config.notifications,
            {
                "all": {
                    "email": [
                        "anna@askanna.io",
                        "robot@askanna.io",
                    ]
                },
                "error": {"email": []},
            },
        )

    def test_notifications_job1(self):
        yml = settings.TEST_RESOURCES_DIR.path("askannaconfig.yml")
        config = AskAnnaConfig.from_stream(open(yml, "r"))

        self.assertEqual(
            config.jobs.get("job1", {}).notifications,
            {
                "all": {
                    "email": [
                        "anna@askanna.io",
                        "robot@askanna.io",
                        "user@askanna.io",
                    ]
                },
                "error": {
                    "email": [
                        "user+error@askanna.io",
                    ]
                },
            },
        )
