import pytest
from django.urls import reverse
from rest_framework import status

from .base_tests import BaseProject

pytestmark = pytest.mark.django_db


class BaseProjectMe(BaseProject):
    def setUp(self):
        super().setUp()
        self.url_private = reverse(
            "project-me",
            kwargs={
                "version": "v1",
                "suuid": self.project_private.suuid,
            },
        )
        self.url_public = reverse(
            "project-me",
            kwargs={
                "version": "v1",
                "suuid": self.project_public.suuid,
            },
        )

        self.url_non_existing = reverse(
            "project-me",
            kwargs={
                "version": "v1",
                "suuid": self.project_private.suuid[:-1] + "1",
            },
        )


class TestProjectMeGet(BaseProjectMe):
    def test_me_as_admin(self):
        """An AskAnna admin doesn't have acces to the project"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_me_as_workspace_admin(self):
        """A workspace admin can get /me on a private project"""
        token = self.users["workspace_admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.remove"] is True  # type: ignore

    def test_me_as_workspace_member(self):
        """A workspace member can get /me on a private project"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.remove"] is False  # type: ignore

    def test_me_as_user_public_project(self):
        """A user can get /me on a public workspace"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.remove"] is False  # type: ignore

    def test_me_as_user_non_existing_project(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_non_existing)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_anonymous_private_project(self):
        """An anonymous user cannot get /me on a private project"""
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_as_anonymous_public_project(self):
        """An anonymous user can get /me on a public project"""
        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.me.view"] is True  # type: ignore
