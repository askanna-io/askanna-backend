import pytest
import requests
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("features/swagger_api.feature")
pytestmark = pytest.mark.django_db


@pytest.fixture
def browser():
    r = requests.Session()
    yield r


@given("AskAnna API-Homepage is available", target_fixture="session")
@pytest.mark.django_db
def aaa_homepage(browser, client):
    response = client.get("/")
    assert response.status_code == 302
    return {}


@when(parsers.parse("the user goes to {where}"))
@pytest.mark.django_db
def goto_api(session, browser, where, client):
    response = client.get("/v1/docs/swagger/")
    session["response"] = response


@then(parsers.parse("the user sees the {where}"))
def findonpage(session, browser, where):
    assert session["response"].status_code == 200
