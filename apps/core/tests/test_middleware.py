import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(DEBUG=True, DEBUG_SQL=True)
def test_debug_sql(client, django_user_model, capfd):
    user = django_user_model.objects.create(  # nosec: B106
        username="john@example.com", email="john@example.com", password="password"
    )
    client.get("/v1/auth/user/", HTTP_AUTHORIZATION="Token %s" % user.auth_token.key)

    captured = capfd.readouterr()

    assert "SELECT" in captured.err
    assert "TOTAL QUERIES" in captured.err


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True, DEBUG_SQL=True)
def test_debug_sql_no_query_part_2(client, capfd):
    client.get("/v1/me/")

    captured = capfd.readouterr()

    assert "SELECT" not in captured.err
    assert "TOTAL QUERIES" not in captured.err


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True, DEBUG_SQL=True)
def test_debug_sql_no_query(client, capfd):
    client.get("/admin/jsi18n/")

    captured = capfd.readouterr()

    assert "SELECT" not in captured.err
    assert "TOTAL QUERIES" not in captured.err


@pytest.mark.django_db
@override_settings(DEBUG=False, DEBUG_SQL=False)
def test_debug_sql_off(client, django_user_model, capfd):
    user = django_user_model.objects.create(  # nosec: B106
        username="john@example.com", email="john@example.com", password="password"
    )
    client.get("/v1/auth/user/", HTTP_AUTHORIZATION="Token %s" % user.auth_token.key)

    captured = capfd.readouterr()

    assert "SELECT" not in captured.err
    assert "TOTAL QUERIES" not in captured.err


@pytest.mark.django_db
@override_settings(DEBUG=True, DEBUG_SQL=False)
def test_debug_sql_with_debug_on_but_sql_debug_off(client, django_user_model, capfd):
    user = django_user_model.objects.create(  # nosec: B106
        username="john@example.com", email="john@example.com", password="password"
    )
    client.get("/v1/auth/user/", HTTP_AUTHORIZATION="Token %s" % user.auth_token.key)

    captured = capfd.readouterr()

    assert "SELECT" not in captured.err
    assert "TOTAL QUERIES" not in captured.err
