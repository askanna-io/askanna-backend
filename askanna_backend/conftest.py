import pytest
from django.conf import settings
from django.test import RequestFactory

from askanna_backend.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath
    settings.IN_TEST_MODE = True


@pytest.fixture
def user() -> settings.AUTH_USER_MODEL:
    return UserFactory()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()
