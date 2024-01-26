import shutil

import pytest

from tests.fixtures.files import *  # noqa: F403
from tests.fixtures.model_objects import *  # noqa: F403
from tests.fixtures.objects import *  # noqa: F403


@pytest.fixture(scope="session")
def temp_dir(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("askanna-test-")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
