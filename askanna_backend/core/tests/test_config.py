import unittest

import pytest
from core.config import AskAnnaConfig
from core.utils.config import get_setting_from_database
from django.conf import settings

pytestmark = pytest.mark.django_db


class TestDatabaseSetting(unittest.TestCase):
    def test_get_setting_from_db(self):
        assert get_setting_from_database("some-setting") is None
        assert get_setting_from_database("some-setting", False) is False
        assert get_setting_from_database("some-setting", True) is True
        assert get_setting_from_database("some-setting", "some-value") == "some-value"

    def test_get_setting_from_db_return_type_bool(self):
        assert get_setting_from_database("some-setting", "True", return_type=bool) is True
        assert get_setting_from_database("some-setting", 1, return_type=bool) is True
        assert get_setting_from_database("some-setting", True, return_type=bool) is True
        with pytest.raises(TypeError):
            get_setting_from_database("some-setting", [True, False], return_type=bool)

    def test_get_setting_from_db_return_type_int(self):
        assert get_setting_from_database("some-setting", "1", return_type=int) == 1
        assert get_setting_from_database("some-setting", 1, return_type=int) == 1
        assert get_setting_from_database("some-setting", True, return_type=int) == 1
        with pytest.raises(TypeError):
            get_setting_from_database("some-setting", [1, 2], return_type=int)

    def test_get_setting_from_db_return_type_str(self):
        assert get_setting_from_database("some-setting", "1", return_type=str) == "1"

    def test_get_actual_setting_from_db(self):
        from core.models import Setting

        Setting.objects.create(name="mock-some-setting", value="some-value")
        assert get_setting_from_database("mock-some-setting", "another-default") == "some-value"


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
