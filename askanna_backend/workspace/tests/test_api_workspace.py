"""Define tests for API of UserProfile."""
from django.utils import timezone
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, User, UserProfile

from ..models import Workspace

pytestmark = pytest.mark.django_db


class BaseWorkspace:
    def setUp(self):
        self.users = {
            "anna": User.objects.create(
                username="anna",
                is_staff=True,
                is_superuser=True,
                email="anna@askanna.dev",
            ),
            "admin": User.objects.create(username="admin"),
            "member": User.objects.create(username="member"),
            "non_member": User.objects.create(username="non_member"),
        }
        self.workspace_a = Workspace.objects.create(name="test workspace a")
        self.workspace_b = Workspace.objects.create(name="test workspace b")
        self.workspace_c = Workspace.objects.create(name="test workspace b")
        self.workspace_d = Workspace.objects.create(name="test workspace b")

        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_a.uuid,
            user=self.users["member"],
            role=WS_MEMBER,
        )
        self.member_profileb = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_b.uuid,
            user=self.users["member"],
            role=WS_MEMBER,
        )
        # make the admin user member of the workspace a
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_a.uuid,
            user=self.users["admin"],
            role=WS_ADMIN,
        )
        # make the admin user member of the workspace b
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_b.uuid,
            user=self.users["admin"],
            role=WS_ADMIN,
        )
        # make the member user deleted member of the workspace
        self.deleted_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_c.uuid,
            user=self.users["member"],
            role=WS_ADMIN,
            deleted=timezone.now(),
        )


class TestWorkspaceListAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workspace-list", kwargs={"version": "v1"})

    def test_list_as_anna(self):
        """
        By default Anna shoudl not be able to list any workspaces.
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_admin(self):
        """
        List the workspace as an admin of the workspace a, but also member of b
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        uuids = [r["uuid"] for r in response.data]
        self.assertIn(str(self.workspace_a.uuid), uuids)
        self.assertIn(str(self.workspace_b.uuid), uuids)

    def test_list_as_member_see_only_its_workspaces(self):
        """A member gets only workspaces it belongs to."""

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        uuids = [r["uuid"] for r in response.data]
        self.assertIn(str(self.workspace_a.uuid), uuids)
        self.assertIn(str(self.workspace_b.uuid), uuids)

    def test_list_as_non_member_see_no_workspaces(self):
        """A user with no memberships see no workspaces."""

        token = self.users["non_member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_nonymous_user_does_not_get_list_of_workspaces(self):
        """A anonymous user has no access to workspace list."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestWorkspaceDetailAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-detail",
            kwargs={"version": "v1", "short_uuid": self.workspace_a.short_uuid},
        )

    def test_detail_as_anna(self):
        """
        By default askanna users cannot see workspace details if not member
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_admin(self):

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_member(self):

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_nonmember(self):

        token = self.users["non_member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestWorkspaceUpdateAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-detail",
            kwargs={"version": "v1", "short_uuid": self.workspace_a.short_uuid},
        )

    def test_update_as_anna(self):
        """
        By default no update possible by askanna users
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_as_admin(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "New workspace name")
        self.assertEqual(response.data.get("description"), "A new world")

    def test_update_as_member(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "New workspace name")
        self.assertEqual(response.data.get("description"), "A new world")

    def test_update_as_member_name(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_details = {"name": "New workspace name 2"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "New workspace name 2")
        self.assertEqual(response.data.get("description"), None)

    def test_update_as_member_description(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_details = {"description": "A new world 2"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "test workspace a")
        self.assertEqual(response.data.get("description"), "A new world 2")

    def test_update_as_nonmember(self):
        token = self.users["non_member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_as_anonymous(self):
        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
