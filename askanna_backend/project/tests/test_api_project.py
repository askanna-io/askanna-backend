"""Define tests for API of invitation workflow."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, User, UserProfile
from workspace.models import Workspace

from ..models import Project

pytestmark = pytest.mark.django_db


class TestProjectFlatAPI(APITestCase):
    def setUp(self):
        self.users = {
            "admin_a": User.objects.create(username="admin_a", is_staff=True, is_superuser=True),
            "member_a": User.objects.create(username="member_a"),
            "user_a": User.objects.create(username="user_a"),
        }
        self.workspace = Workspace.objects.create(title="test workspace")
        self.project = Project.objects.create(name="test project", workspace=self.workspace)

        self.unused_workspace = Workspace.objects.create(title="unused workspace")
        self.unused_project = Project.objects.create(name="unused project", workspace=self.unused_workspace)

        # make the admin user member of the workspace
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_a"],
            role=WS_ADMIN,
        )
        # make the member_a user member of the workspace
        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
        )

    def test_member_can_get_project(self):
        """A member of the workspace can get a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"short_uuid": self.project.short_uuid}.items() <= dict(response.data).items())

    def test_admin_can_get_project(self):
        """An admin of the workspace can get a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"short_uuid": self.project.short_uuid}.items() <= dict(response.data).items())

    def test_non_member_cannot_get_project(self):
        """Non member do not have access to the project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_get_project(self):
        """An anonymous user do not have access to the project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_create_project(self):
        """A member of the workspace can create a project."""
        url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"workspace": self.workspace.short_uuid, "name": "new created project"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_create_project(self):
        """An admin of the workspace can create a project."""
        url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"workspace": self.workspace.short_uuid, "name": "new created project"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_member_cannot_create_project(self):
        """Non member can not create projects."""
        url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"workspace": self.workspace.short_uuid, "name": "new created project"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_create_project(self):
        """An anonymous user cannot create projects."""
        url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

        response = self.client.post(
            url, {"workspace": self.workspace.short_uuid, "name": "new created project"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_update_project(self):
        """A member of the workspace can update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(url, {"name": "a new name", "workspace": self.workspace.short_uuid}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a new name"}.items() <= dict(response.data).items())

    def test_admin_can_update_project(self):
        """An admin of the workspace can update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(url, {"name": "a new name", "workspace": self.workspace.short_uuid}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a new name"}.items() <= dict(response.data).items())

    def test_non_member_cannot_update_project(self):
        """Non member can not update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(url, {"name": "a new name", "workspace": self.workspace.short_uuid}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_update_project(self):
        """An anonymous user can not update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        response = self.client.put(url, {"name": "a new name", "workspace": self.workspace.short_uuid}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_partially_update_project(self):
        """A member of the workspace can partially update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a partial new name"}.items() <= dict(response.data).items())

    def test_admin_can_partially_update_project(self):
        """An admin of the workspace can partially update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a partial new name"}.items() <= dict(response.data).items())

    def test_non_member_cannot_partially_update_project(self):
        """Non member can not partially update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_partially_update_project(self):
        """An anonymous user can not partially update a project."""
        url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

        response = self.client.patch(url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
