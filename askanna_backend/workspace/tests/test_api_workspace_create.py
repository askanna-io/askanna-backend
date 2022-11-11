"""Define tests for API of UserProfile."""
import pytest
from core.tests.base import BaseUserPopulation
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import MSP_WORKSPACE, WS_ADMIN, Membership, UserProfile
from workspace.models import Workspace

pytestmark = pytest.mark.django_db


class BaseWorkspace(BaseUserPopulation):
    def setUp(self):
        super().setUp()


class TestWorkspaceCreateAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workspace-list", kwargs={"version": "v1"})

    def test_create_workspace_as_anonymous_not_allowed(self):
        """An anonumous person can not create a workspace."""
        new_workspace = {"name": "New workspace name"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_workspace_as_anna(self):
        """An member without access to a workspace can create a workspace."""
        self.activate_user("anna")

        new_workspace = {"name": "New workspace name for anna"}
        response = self.client.post(self.url, new_workspace, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("name"), "New workspace name for anna")
        self.assertEqual(response.data.get("visibility"), "PRIVATE")

    def test_create_workspace_as_admin(self):
        """An admin can create a workspace."""
        self.activate_user("admin")

        new_workspace = {"name": "New workspace name for admin"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("name"), "New workspace name for admin")
        self.assertEqual(response.data.get("visibility"), "PRIVATE")

    def test_create_workspace_as_member(self):
        """A member can create a workspace."""
        self.activate_user("member")

        new_workspace = {"name": "New workspace name for member"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("name"), "New workspace name for member")
        self.assertEqual(response.data.get("visibility"), "PRIVATE")

    def test_create_workspace_with_missing_name(self):
        """If name of the new workspace is missing, don't create the workspace"""
        self.activate_user("member")

        new_workspace = {"description": "Only a description"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_workspace_with_empty_name(self):
        """If name of the new workspace is empty, don't create the workspace"""
        self.activate_user("member")

        new_workspace = {"name": ""}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_workspace_set_visibility_private(self):
        """At creation of new workspace we can set the visibility to private"""
        self.activate_user("member")

        new_workspace = {"name": "New workspace name for member", "visibility": "PRIVATE"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("name"), "New workspace name for member")
        self.assertEqual(response.data.get("visibility"), "PRIVATE")

    def test_create_workspace_set_visibility_public(self):
        """At creation of new workspace we can set the visibility to public"""
        self.activate_user("member")

        new_workspace = {"name": "New workspace name for member", "visibility": "PUBLIC"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("name"), "New workspace name for member")
        self.assertEqual(response.data.get("visibility"), "PUBLIC")

    def test_create_workspace_with_invalid_visibility(self):
        """At creation of new workspace we validate the visibility"""
        self.activate_user("member")

        new_workspace = {"name": "New workspace name", "visibility": "UNVALID_OPTION"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_workspace_set_created_by(self):
        """A member is set as the creator of the workspace"""
        self.activate_user("member")
        user = self.users["member"]

        new_workspace = {"name": "New workspace name for member"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        suuid = response.data["suuid"]
        workspace = Workspace.objects.get(suuid=suuid)

        self.assertIsNotNone(workspace)
        self.assertEqual(workspace.created_by, user)

    def test_create_workspace_membership_and_userprofile(self):
        """A member gets a membership in the workspace that was greated by the member"""
        self.activate_user("member")
        user = self.users["member"]

        new_workspace = {"name": "New workspace name for member"}
        response = self.client.post(self.url, new_workspace, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        suuid = response.data["suuid"]
        workspace = Workspace.objects.get(suuid=suuid)

        membership = Membership.objects.get(object_uuid=workspace.uuid, object_type=MSP_WORKSPACE, user=user)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, WS_ADMIN)

        userprofile = UserProfile.objects.get(object_uuid=workspace.uuid, object_type=MSP_WORKSPACE, user=user)
        self.assertEqual(userprofile.uuid, membership.uuid)
        self.assertEqual(userprofile.role, membership.role)
