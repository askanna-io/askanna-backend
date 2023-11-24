import pytest
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db


class AskAnnaAPITestCase(APITestCase):
    def set_authorization(self, user):
        if hasattr(user, "auth_token"):
            token = user.auth_token
        elif hasattr(self, "users"):
            token = self.users.get(user).auth_token
        else:
            raise ValueError(f"User '{user}' not found")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
