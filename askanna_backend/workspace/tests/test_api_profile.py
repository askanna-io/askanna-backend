import pytest
from account.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, UserProfile
from core.tests.base import BaseUserPopulation
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from workspace.listeners import install_demo_project_in_workspace

from ..models import Workspace

pytestmark = pytest.mark.django_db


class TestProfileAPI(BaseUserPopulation, APITestCase):
    def setUp(self):
        super().setUp()
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)

    def test_member_can_not_change_other_member_profile(self):
        """A profile can not be changed by a non owner."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member2").suuid,
            },
        )

        token = self.users.get("member").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_is_restricted_to_correct_workspace(self):
        """An admin in one workspace is not an admin in another."""
        new_workspace = Workspace.objects.create(name="test workspace")
        new_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=new_workspace.uuid,
            user=self.users["admin2"],
            role=WS_ADMIN,
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": new_workspace.suuid,
                "suuid": new_profile.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"role_code": WS_ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_is_restricted_to_correct_workspace(self):
        """An member in one workspace can not see a member in another."""
        new_workspace = Workspace.objects.create(name="test workspace")
        new_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=new_workspace.uuid,
            user=self.users["member2"],
            role=WS_MEMBER,
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": new_workspace.suuid,
                "suuid": new_profile.suuid,
            },
        )

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_not_change_other_member_job_title(self):
        """The job_title field can not be changed by other non admin user."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member2").suuid,
            },
        )

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_change_own_job_title(self):
        """The job_title field of a member can be changed by the member itself."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "a new job title")

    def test_member_can_change_own_name(self):
        """The name field of a member can be changed by the member itself."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users["member"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"name": "my new name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "my new name")

    def test_admin_can_change_other_member_job_title(self):
        """The job_title field can be changed by an admin."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "a new job title")

    def test_admin_can_change_own_job_title(self):
        """The job_title of an admin can be changed by the admin itself."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin").suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "a new job title")

    def test_change_role_as_admin_works(self):
        """An admin can change the profile of a member to admin."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"role_code": WS_ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserProfile.objects.get(pk=self.members.get("member").pk).role, WS_ADMIN)

    def test_change_role_as_member_fails(self):
        """A member can not change the profile of a member to admin."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users["member2"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"role_code": WS_ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_admin_role_as_admin_works(self):
        """An admin can change the profile of another admin to member."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin2").suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"role_code": WS_MEMBER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserProfile.objects.get(pk=self.members.get("admin2").pk).role, WS_MEMBER)

    def test_change_admin_role_by_self_fails(self):
        """An admin can not itself change its role."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin").suuid,
            },
        )

        token = self.users.get("admin").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"role_code": WS_MEMBER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_admin_role_as_member_fails(self):
        """A member can not change the profile of a admin to member."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin").suuid,
            },
        )

        token = self.users.get("member2").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"role_code": WS_MEMBER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_profile_requires_correct_workspace(self):
        """The path to a profile requires the correct parrent be given."""
        workspace_to_fail = Workspace.objects.create(name="workspace to fail")

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": workspace_to_fail.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_profile_as_anonymous_fails(self):
        """Anonymous users can not see profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_as_non_member_fails(self):
        """Non members can not see profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users.get("non_member").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_profile_as_member(self):
        """A member can see existing profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users.get("member2").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"suuid": self.members.get("member").suuid}.items() <= dict(response.data).items())

    def test_retrieve_profile_as_admin(self):
        """An admin can see existing profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users.get("admin").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"suuid": self.members.get("member").suuid}.items() <= dict(response.data).items())

    def test_list_limited_to_current_workspace(self):
        """Listing of people is correctly filtered to requested workspace."""
        new_workspace = Workspace.objects.create(name="test workspace")
        filtered_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=new_workspace.uuid,
            user=self.users.get("member"),
            role=WS_ADMIN,
        )

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
            },
        )

        token = self.users.get("admin").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        suuids = [p["suuid"] for p in response.data["results"]]
        self.assertEqual(len(suuids), 6)
        self.assertNotIn(str(filtered_profile.pk), suuids)
        self.assertIn(str(self.members.get("member2").suuid), suuids)


class TestDeletedProfileAPI(BaseUserPopulation, APITestCase):
    def setUp(self):
        super().setUp()

    def test_deleted_member_is_denied_access_to_list(self):
        """A soft-deleted Profile has no access to the profiles of a workspace."""
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
            },
        )

        token = self.users.get("member_inactive").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_member_is_denied_access_to_profile(self):
        """A user with a soft-deleted profile can not retrieve its own profile."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member_inactive").suuid,
            },
        )

        token = self.users.get("member_inactive").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_member_is_denied_access_to_edit_profile(self):
        """A user with a soft-deleted profile can not edit its own profile.
        When an profile is deleted, this cannot be accessed anymore (404 not found)"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member_inactive").suuid,
            },
        )

        token = self.users.get("member_inactive").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        with self.subTest("empty payload"):
            response = self.client.patch(
                url,
                {},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        with self.subTest("job_title"):
            response = self.client.patch(
                url,
                {"job_title": "A new title"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_admin_is_denied_access_to_list(self):
        """A soft-deleted admin Profile has no access to the profiles of a workspace."""
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
            },
        )

        token = self.users.get("admin_inactive").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_admin_is_denied_access_to_profile(self):
        """An admin with a soft-deleted profile can not retrieve its own profile.
        When an profile is deleted, this cannot be accessed anymore (404 not found)"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin_inactive").suuid,
            },
        )

        token = self.users.get("admin_inactive").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_admin_is_denied_access_to_edit_profile(self):
        """An admin with a soft-deleted profile can not edit its own profile.
        When an profile is deleted, this cannot be accessed anymore (404 not found)"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin_inactive").suuid,
            },
        )

        token = self.users.get("admin_inactive").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        with self.subTest("empty payload"):
            response = self.client.patch(
                url,
                {},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        with self.subTest("job_title"):
            response = self.client.patch(
                url,
                {"job_title": "A new title"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRemovingProfile(BaseUserPopulation, APITestCase):
    def setUp(self):
        super().setUp()
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)

    def test_admin_can_remove_profile(self):
        """Admins of a workspace can remove a member from it."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin2").suuid,
            },
        )

        token = self.users.get("admin").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        before_delete = timezone.now()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertGreater(
            UserProfile.objects.filter(uuid=self.members.get("admin2").uuid).first().deleted_at,
            before_delete,
        )

    def test_member_cannot_remove_profile(self):
        """Members of a workspace cannot remove a member from it."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users.get("member2").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(UserProfile.objects.filter(uuid=self.members.get("member").uuid).first().deleted_at)

    def test_non_member_cannot_remove_profile(self):
        """Non members of a workspace cannot remove profiles from it."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("member").suuid,
            },
        )

        token = self.users.get("non_member").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(UserProfile.objects.filter(uuid=self.members.get("member").uuid).first().deleted_at)

    def test_admin_cannot_remove_profiles_from_other_workspace(self):
        """Removing a profile is limited to workspaces an admin is member of."""
        extra_workspace = Workspace.objects.create(name="extra test workspace")
        extra_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=extra_workspace.uuid,
            user=self.users.get("member3"),
            role=WS_MEMBER,
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": extra_workspace.suuid,
                "suuid": extra_profile.suuid,
            },
        )

        token = self.users.get("admin").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(UserProfile.objects.filter(uuid=extra_profile.uuid).first().deleted_at)

    def test_admin_cannot_remove_self_profile(self):
        """An admin an not remove its own profile from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace_a.suuid,
                "suuid": self.members.get("admin").suuid,
            },
        )

        token = self.users.get("admin").auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(UserProfile.objects.filter(uuid=self.members.get("admin").uuid).first().deleted_at)
