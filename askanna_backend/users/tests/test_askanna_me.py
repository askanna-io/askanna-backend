import pytest
from django.urls import reverse
from rest_framework import status

from .base_tests import BaseAccounts

pytestmark = pytest.mark.django_db


class BaseMe(BaseAccounts):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "askanna-me",
            kwargs={
                "version": "v1",
            },
        )


class TestMeGet(BaseMe):
    """Test to retrieve `/v1/me/`"""

    def test_me_as_admin(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is True
        assert permissions.get("askanna.member") is True

    def test_me_as_user(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_anonymous(self):
        """
        As anonymous user we also get a "me" profile
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is False


class TestMePatch(BaseMe):
    """Test to update AskAnna user profile via `/v1/me/`"""

    def test_me_as_admin(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "new name"  # type: ignore
        assert response.data["job_title"] == "new title"  # type: ignore

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is True
        assert permissions.get("askanna.member") is True

    def test_me_as_user(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "new name"  # type: ignore
        assert response.data["job_title"] == "new title"  # type: ignore

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_anonymous(self):
        """Anonymous cannot update /me"""
        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_as_user_partial_name(self):
        """Regular user can update /me with only name"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "name": "new partial name",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "new partial name"  # type: ignore

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_user_partial_jobtitle(self):
        """Regular user can update /me with only job_title"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "job_title": "new partial title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["job_title"] == "new partial title"  # type: ignore

        permissions = response.data["permission"]  # type: ignore
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True


class TestMeDelete(BaseMe):
    """Test to delete user account via /v1/me/"""

    def test_me_as_admin(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_me_as_user(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_me_as_anonymous(self):
        """
        Anonymous cannot delete /me
        """
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
