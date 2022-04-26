"""Define tests for API of UserProfile."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.tests.base import BaseUserPopulation

pytestmark = pytest.mark.django_db


class BaseWorkspace(BaseUserPopulation):
    def setUp(self):
        super().setUp()


class TestWorkspaceListAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workspace-list", kwargs={"version": "v1"})

    def test_list_as_anna(self):
        """
        By default Anna should only list public workspaces
        """
        self.activate_user("anna")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_admin(self):
        """
        List the workspace as an admin of the workspace a, but also member of b
        """
        self.activate_user("admin")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        uuids = [r["uuid"] for r in response.json()]
        self.assertIn(str(self.workspace_a.uuid), uuids)
        self.assertIn(str(self.workspace_b.uuid), uuids)

    def test_list_as_member_see_only_its_workspaces(self):
        """A member gets only workspaces it belongs to and public workspaces"""
        self.activate_user("member")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        uuids = [r["uuid"] for r in response.json()]
        self.assertIn(str(self.workspace_a.uuid), uuids)

        for r in response.data:
            # make sure we have an "is_member" for each workspace
            self.assertFalse(r.get("is_member") is None)

    def test_list_as_non_member_see_no_workspaces(self):
        """A user with no memberships see only public workspaces."""
        self.activate_user("non_member")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_nonymous_user_does_not_get_list_of_workspaces(self):
        """A anonymous user has no access to workspace list."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestWorkspaceDetailAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-detail",
            kwargs={"version": "v1", "short_uuid": self.workspace_a.short_uuid},
        )
        self.url_non_existing_workspace = reverse(
            "workspace-detail",
            kwargs={"version": "v1", "short_uuid": self.workspace_a.short_uuid[:-1] + "a"},
        )

    def test_detail_as_anna(self):
        """
        By default askanna users cannot see workspace details if not member
        """
        self.activate_user("anna")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_as_admin(self):
        self.activate_user("admin")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_member(self):
        self.activate_user("member")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_workspaceviewer(self):
        self.activate_user("member_wv")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_nonmember(self):
        self.activate_user("non_member")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_as_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_member_invalid_workspace_uuid(self):
        self.activate_user("member")

        response = self.client.get(self.url_non_existing_workspace)
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_workspaceviewer_public_project_other_public_workspace(self):
        """
        Case: public workspace, private project. User is workspace viewer ( not on this workspace )

        The project list returns all projects, public and private.

        Also, I could call get project API point.

        Expected: return only public projects.
        """
        self.activate_user("member_wv")

        url = reverse(
            "workspace-detail",
            kwargs={"version": "v1", "short_uuid": self.workspace_c.short_uuid},
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "test workspace_c")


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
        self.activate_user("anna")

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_admin(self):
        self.activate_user("admin")

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "New workspace name")
        self.assertEqual(response.data.get("description"), "A new world")

    def test_update_as_member(self):
        self.activate_user("member")

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_member_name(self):
        self.activate_user("member")

        new_details = {"name": "New workspace name 2"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_member_description(self):
        self.activate_user("member")

        new_details = {"description": "A new world 2"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_member_visibility(self):
        self.activate_user("member")

        new_details = {"visibility": "PUBLIC"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_admin_visibility(self):
        self.activate_user("admin")

        new_details = {"visibility": "PUBLIC"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("visibility"), "PUBLIC")

    def test_update_as_nonmember(self):
        self.activate_user("non_member")

        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_anonymous(self):
        new_details = {"name": "New workspace name", "description": "A new world"}

        response = self.client.patch(self.url, new_details, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestWorkspaceDeleteAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-detail",
            kwargs={"version": "v1", "short_uuid": self.workspace_a.short_uuid},
        )

    def test_delete_as_anna(self):
        """
        By default no deletion possible by askanna users
        """
        self.activate_user("anna")

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_admin(self):
        """
        Workspace members can delete a workspace
        """
        self.activate_user("admin")

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_as_member(self):
        """
        Delete a workspace by a member is not possible
        """
        self.activate_user("member")

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_non_member(self):
        """
        Non members cannot delete a workspace, also we cannot find the workspace at all
        """
        self.activate_user("non_member")

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_anonymous(self):
        """
        Anonymous users cannot delete a workspace
        """
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestWorkspaceListWithFilterAPI(BaseWorkspace, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workspace-list", kwargs={"version": "v1"})

    def test_list_as_anna(self):
        """
        By default Anna should only list public workspaces and cannot see
        other workspaces
        """
        self.activate_user("anna")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_admin(self):
        """
        List the workspace as an admin of the workspace a, but also member of b
        """
        self.activate_user("admin")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # also test ordering, only possible with test admin account as this has 3 workspaces to list all
        response = self.client.get(self.url, {"ordering": "membership"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(self.url, {"ordering": "-membership"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(self.url, {"ordering": "-membership,-created"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_as_member_see_only_its_workspaces(self):
        """A member gets only workspaces it belongs to and public workspaces"""
        self.activate_user("member")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_non_member_see_no_workspaces(self):
        """A user will only see public projects"""
        self.activate_user("non_member")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_nonymous_user_does_not_get_list_of_workspaces(self):
        """A anonymous user will only see public project in the list."""

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
