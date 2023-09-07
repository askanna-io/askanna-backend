import pytest
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db


class AskAnnaAPITestCASE(APITestCase):
    def set_authorization(self, user):
        token = user.auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
