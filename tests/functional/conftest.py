"""Functional tests configuration."""
import os.path
import pytest


@pytest.fixture
def pytestbdd_feature_base_dir():
    """Basedir for feature files."""
    return os.path.join(os.path.dirname(__file__), "features")

