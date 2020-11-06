from django.urls import reverse
import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from workspace.models import Workspace
from workspace.views import PersonViewSet
from users.models import User

pytestmark = pytest.mark.django_db


class BaseUsers:
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

    @classmethod
    def teardown_class(cls):
        """
        Remove all the user instances we had setup for the test
        """
        for _, user in cls.users.items():
            user.delete()


class TestUserListAPI(BaseUsers, APITestCase):
    """
    Testing the list function for the /v1/accounts/
    """

    def setUp(self):
        self.url = reverse("user-list", kwargs={"version": "v1"},)

    def test_list_users_as_admin(self):
        """
        We can list users as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_as_normaluser(self):
        """
        We can list users as a normal user
        """
        token = self.users["userB"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_anonymous(self):
        """
        We cannot list users as anonymous user
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestUserCreateAPI(BaseUsers, APITestCase):
    """
    Testing the create function for the /v1/accounts/
    """

    def setUp(self):
        self.url = reverse("user-list", kwargs={"version": "v1"},)

    def test_create_user_as_admin(self):
        """
        We can create an user as admin/superuser
        """

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "admin-test@askanna.dev",
                "username": "admin-test@askanna.dev",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cleanup via internal functions
        User.objects.get(short_uuid=response.data["short_uuid"]).delete()

    def test_create_user_as_normaluser(self):
        """
        We should not be able to create an user as normal user
        """
        # FIXME: should check the business rule for this particular test
        token = self.users["userB"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "user-test@askanna.dev",
                "username": "user-test@askanna.dev",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_as_anonymous(self):
        """
        We can create an user as anonymous (new member signup)
        """
        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "anon-test@askanna.dev",
                "username": "anon-test@askanna.dev",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cleanup via internal functions
        User.objects.get(short_uuid=response.data["short_uuid"]).delete()
