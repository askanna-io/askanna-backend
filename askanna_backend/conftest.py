import pytest
from django.conf import settings  # noqa: 401


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):  # noqa: F811
    settings.MEDIA_ROOT = tmpdir.strpath
