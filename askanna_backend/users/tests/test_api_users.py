import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


from workspace.models import Workspace
from workspace.views import PersonViewSet
from users.models import User

pytestmark = pytest.mark.django_db


class TestUserAPI(APITestCase):
    @classmethod
    def setup_class(cls):
        cls.users = {
            "admin": User.objects.create(
                username="admin2",
                is_staff=True,
                is_superuser=True,
                email="admin2@askanna.dev",
            ),
            "userB": User.objects.create(username="userB", email="userB@askanna.dev"),
        }

    def test_list_users_as_admin(self):
        """
        We can list users as an admin user
        """
        url = reverse("user-list", kwargs={"version": "v1"},)

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_as_normaluser(self):
        """
        We can list users as a normal user
        """
        url = reverse("user-list", kwargs={"version": "v1"},)

        token = self.users["userB"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_a_anonymous(self):
        """
        We can list users as a normal user
        """
        url = reverse("user-list", kwargs={"version": "v1"},)

        response = self.client.get(url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

