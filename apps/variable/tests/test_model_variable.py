import pytest

from variable.models import Variable

pytestmark = pytest.mark.django_db


def test_variable_active(test_variables):
    assert Variable.objects.active().count() == 4
    test_variables["variable_private"].to_deleted()
    assert Variable.objects.active().count() == 3


def test_variable_inactive(test_variables):
    assert Variable.objects.inactive().count() == 0
    test_variables["variable_private"].to_deleted()
    assert Variable.objects.inactive().count() == 1


def test_masked(db):
    variable = Variable(**{"name": "test", "value": "secret", "is_masked": True})
    assert variable.get_value() == "***masked***"
    assert variable.value == "secret"
    assert variable.is_masked is True
