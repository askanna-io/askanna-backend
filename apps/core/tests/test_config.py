import unittest

import pytest
from django.conf import settings

from core.config import AskAnnaConfig
from core.utils.config import get_setting

pytestmark = pytest.mark.django_db


class TestDatabaseSetting(unittest.TestCase):
    def test_get_setting(self):
        assert get_setting("some-setting") is None
        assert get_setting("some-setting", default=False, return_type=bool) is False
        assert get_setting("some-setting", default=True, return_type=bool) is True
        assert get_setting("some-setting", default="some-value") == "some-value"
        with pytest.raises(TypeError):
            get_setting("some-setting", default=[1, 2, 3])
        assert get_setting("some-setting", default=[1, 2, 3], return_type=list) == [1, 2, 3]

    def test_get_setting_return_type_bool(self):
        assert get_setting("some-setting", default="True", return_type=bool) is True
        assert get_setting("some-setting", default=1, return_type=bool) is True
        assert get_setting("some-setting", default=True, return_type=bool) is True
        with pytest.raises(TypeError):
            get_setting("some-setting", default=[True, False], return_type=bool)

    def test_get_setting_return_type_int(self):
        assert get_setting("some-setting", default="1", return_type=int) == 1
        assert get_setting("some-setting", default=1, return_type=int) == 1
        assert get_setting("some-setting", default=True, return_type=int) == 1
        with pytest.raises(TypeError):
            get_setting("some-setting", default=[1, 2], return_type=int)

    def test_get_setting_return_type_float(self):
        assert get_setting("some-setting", default="1.1", return_type=float) == 1.1
        assert get_setting("some-setting", default=2.1, return_type=float) == 2.1
        assert get_setting("some-setting", default=True, return_type=float) == 1
        with pytest.raises(TypeError):
            get_setting("some-setting", default=[1.1, 2.1], return_type=float)

    def test_get_setting_return_type_str(self):
        assert get_setting("some-setting", default="1", return_type=str) == "1"

    def test_get_actual_setting_from_db(self):
        from core.models import Setting

        Setting.objects.create(name="mock-some-setting", value="some-value")
        assert get_setting("mock-some-setting", default="another-default") == "some-value"


class TestAskAnnaConfig(unittest.TestCase):
    def test_notifications_global(self):
        yml = settings.TEST_RESOURCES_DIR / "askannaconfig.yml"
        config = AskAnnaConfig.from_stream(yml.open())

        assert config is not None
        assert config.notifications == {
            "all": {
                "email": [
                    "anna@askanna.io",
                    "robot@askanna.io",
                ]
            },
            "error": {"email": []},
        }

    def test_notifications_job1(self):
        yml = settings.TEST_RESOURCES_DIR / "askannaconfig.yml"
        config = AskAnnaConfig.from_stream(yml.open())

        assert config is not None
        assert config.jobs.get("job1", {}) != {}
        assert config.jobs.get("job1", {}) is not None
        assert config.jobs.get("job1", {}).notifications == {
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
        }
