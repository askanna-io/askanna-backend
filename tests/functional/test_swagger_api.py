import pytest
import requests

from pytest_bdd import scenarios, given, when, then, parsers


# Scenarios
scenarios("features/swagger_api.feature")
pytestmark = pytest.mark.django_db


# Fixtures


@pytest.fixture
def browser():
    r = requests.Session()
    yield r


# Given steps


@given("AskAnna API-Homepage is available", target_fixture="session")
@pytest.mark.django_db
def aaa_homepage(browser, client):
    response = client.get("/")
    return {}


# When steps


@when(parsers.parse("the user goes to {where}"))
@pytest.mark.django_db
def goto_api(session, browser, where, client):
    response = client.get("/v1/docs/swagger/")
    session["response"] = response


# Then steps


@then(parsers.parse("the user sees the {where}"))
def findonpage(session, browser, where):
    assert session["response"].status_code == 200
