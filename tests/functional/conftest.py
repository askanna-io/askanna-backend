"""Functional tests configuration."""
from pathlib import Path

import pytest


@pytest.fixture
def pytestbdd_feature_base_dir():
    """Basedir for feature files."""
    return Path(__file__).parent / "features"
