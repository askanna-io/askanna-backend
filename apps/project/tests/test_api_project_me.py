import pytest
from django.urls import reverse
from rest_framework import status

from core.utils.suuid import create_suuid
from tests import AskAnnaAPITestCASE


class BaseProjectMeAPI(AskAnnaAPITestCASE):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_workspaces, test_memberships, test_projects):
        self.users = test_users
        self.workspaces = test_workspaces
        self.memberships = test_memberships
        self.projects = test_projects

    def setUp(self):
        super().setUp()
        self.url_private = reverse(
            "project-me",
            kwargs={
                "version": "v1",
                "suuid": self.projects["project_private"].suuid,
            },
        )
        self.url_public = reverse(
            "project-me",
            kwargs={
                "version": "v1",
                "suuid": self.projects["project_public"].suuid,
            },
        )

        self.url_non_existing = reverse(
            "project-me",
            kwargs={
                "version": "v1",
                "suuid": create_suuid(),
            },
        )


class TestProjectMeGet(BaseProjectMeAPI):
    def test_me_as_superuser(self):
        """A superuser user doesn't have acces to the project where the user is not a member"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_workspace_admin(self):
        """A workspace admin can get /me on a private project if the user is a member of the workspace"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.remove"] is True  # type: ignore

    def test_me_as_workspace_member(self):
        """A workspace member can get /me on a private project if the user is a member of the workspace"""
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.remove"] is False  # type: ignore
        assert response.data["permission"]["project.run.edit"] is True  # type: ignore

    def test_me_as_user_public_project(self):
        """A user can get /me on a public workspace"""
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url_public)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.remove"] is False  # type: ignore
        assert response.data["permission"]["project.run.edit"] is False  # type: ignore

    def test_me_as_user_private_project(self):
        """A user can get /me on a public workspace"""
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url_private)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_user_non_existing_project(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url_non_existing)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_anonymous_private_project(self):
        """An anonymous user cannot get /me on a private project"""
        self.client.credentials()  # type: ignore

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_anonymous_public_project(self):
        """An anonymous user can get /me on a public project"""
        self.client.credentials()  # type: ignore

        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["project.me.view"] is True  # type: ignore
