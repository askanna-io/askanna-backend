"""Define tests for API of UserProfile."""
from django.utils import timezone
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, User, UserProfile

from ..models import Workspace

pytestmark = pytest.mark.django_db


class TestWorkspaceAPI(APITestCase):
    def setUp(self):
        self.users = {
            "member": User.objects.create(username="member"),
            "non_member": User.objects.create(username="non_member"),
        }
        self.workspace_a = Workspace.objects.create(title="test workspace a")
        self.workspace_b = Workspace.objects.create(title="test workspace b")
        self.workspace_c = Workspace.objects.create(title="test workspace b")
        self.workspace_d = Workspace.objects.create(title="test workspace b")

        # make the member user admin of the workspace
        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_a.uuid,
            user=self.users["member"],
            role=WS_ADMIN,
        )
        # make the member user member of the workspace
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_b.uuid,
            user=self.users["member"],
            role=WS_MEMBER,
        )
        # make the member user deleted member of the workspace
        self.deleted_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace_c.uuid,
            user=self.users["member"],
            role=WS_ADMIN,
            deleted=timezone.now()
        )

    def test_anonymous_user_does_not_get_list_of_workspaces(self):
        """A anonymous user has no access to workspace list."""
        url = reverse(
            "workspace-list",
            kwargs={
                "version": "v1",
            },
        )

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_member_see_no_workspaces(self):
        """A user with no memberships see no workspaces."""
        url = reverse(
            "workspace-list",
            kwargs={
                "version": "v1",
            },
        )

        token = self.users["non_member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_member_see_only_its_workspaces(self):
        """A member gets only workspaces it belongs to."""
        url = reverse(
            "workspace-list",
            kwargs={
                "version": "v1",
            },
        )

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        uuids = [r["uuid"] for r in response.data]
        self.assertIn(str(self.workspace_a.uuid), uuids)
        self.assertIn(str(self.workspace_b.uuid), uuids)
