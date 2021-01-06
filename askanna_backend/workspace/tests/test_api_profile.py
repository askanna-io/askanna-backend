"""Define tests for API of UserProfile."""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, User, UserProfile

from ..models import Workspace

pytestmark = pytest.mark.django_db


class TestProfileAPI(APITestCase):
    def setUp(self):
        self.users = {
            "admin_a": User.objects.create(username="admin_a"),
            "admin_b": User.objects.create(username="admin_b"),
            "member_a": User.objects.create(username="member_a"),
            "member_b": User.objects.create(username="member_b"),
            "user_a": User.objects.create(username="user_a"),
        }
        self.workspace = Workspace.objects.create(title="test workspace")

        # make the admin_a user member of the workspace
        self.admin_a_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_a"],
            role=WS_ADMIN,
        )
        # make the admin_b user member of the workspace
        self.admin_b_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_b"],
            role=WS_ADMIN,
        )
        # make the member_a user member of the workspace
        self.member_a_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
        )
        # make the member_b user member of the workspace
        self.member_b_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_b"],
            role=WS_MEMBER,
        )

    def test_member_can_not_change_other_member_profile(self):
        """A profile can not be changed by a non owner."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_b_profile.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_is_restricted_to_correct_workspace(self):
        """An admin in one workspace is not an admin in another."""
        new_workspace = Workspace.objects.create(title="test workspace")
        new_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=new_workspace.uuid,
            user=self.users["admin_b"],
            role=WS_ADMIN,
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": new_workspace.short_uuid,
                "short_uuid": new_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"role": WS_ADMIN}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_is_restricted_to_correct_workspace(self):
        """An member in one workspace can not see a member in another."""
        new_workspace = Workspace.objects.create(title="test workspace")
        new_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=new_workspace.uuid,
            user=self.users["member_b"],
            role=WS_MEMBER,
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": new_workspace.short_uuid,
                "short_uuid": new_profile.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_not_change_other_member_job_title(self):
        """The job_title field can not be changed by other non admin user."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_b_profile.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url, {"job_title": "a new job title"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_change_own_job_title(self):
        """The job_title field of a member can be changed by the member itself."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url, {"job_title": "a new job title"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "a new job title")

    def test_member_can_change_own_name(self):
        """The name field of a member can be changed by the member itself."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"name": "my new name"}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "my new name")

    def test_admin_can_change_other_member_job_title(self):
        """The job_title field can be changed by an admin."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url, {"job_title": "a new job title"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "a new job title")

    def test_admin_can_change_own_job_title(self):
        """The job_title of an admin can be changed by the admin itself."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_a_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url, {"job_title": "a new job title"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "a new job title")

    def test_change_role_as_admin_works(self):
        """An admin can change the profile of a member to admin."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"role": WS_ADMIN}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            UserProfile.objects.get(pk=self.member_a_profile.pk).role, WS_ADMIN
        )

    def test_change_role_as_member_fails(self):
        """A member can not change the profile of a member to admin."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["member_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"role": WS_ADMIN}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_admin_role_as_admin_works(self):
        """An admin can change the profile of another admin to member."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_b_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"role": WS_MEMBER}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            UserProfile.objects.get(pk=self.member_b_profile.pk).role, WS_MEMBER
        )

    def test_change_admin_role_by_self_fails(self):
        """An admin can not itself change its role."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_a_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"role": WS_MEMBER}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_admin_role_as_member_fails(self):
        """A member can not change the profile of a admin to member."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_a_profile.short_uuid,
            },
        )

        token = self.users["member_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"role": WS_MEMBER}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_profile_requires_correct_workspace(self):
        """The path to a profile requires the correct parent be given."""
        workspace_to_fail = Workspace.objects.create(title="workspace to fail")

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": workspace_to_fail.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        response = self.client.get(url,)
        # 401 is raised and not 404 as the permission check at the workspace level
        # comes before than the loading of the profile.
        # Since the user does not belong to the given workspace, it fails.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_as_anonymous_fails(self):
        """Anonymous users can not see profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_as_non_member_fails(self):
        """Non members can not see profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_profile_as_member(self):
        """A member can see existing profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["member_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.member_a_profile.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_retrieve_profile_as_admin(self):
        """An admin can see existing profiles from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.member_a_profile.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_list_limited_to_current_workspace(self):
        """Listing of people is correctly filtered to requested workspace."""
        new_workspace = Workspace.objects.create(title="test workspace")
        filtered_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=new_workspace.uuid,
            user=self.users["member_a"],
            role=WS_ADMIN,
        )

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        uuids = [p["uuid"] for p in response.data]
        self.assertEqual(len(uuids), 4)
        self.assertNotIn(str(filtered_profile.pk), uuids)
        self.assertIn(str(self.member_b_profile.pk), uuids)


class TestDeletedProfileAPI(APITestCase):
    def setUp(self):
        self.users = {
            "admin_a_deleted_profile": User.objects.create(
                username="admin_a_deleted_profile"
            ),
            "member_a_deleted_profile": User.objects.create(
                username="member_a_deleted_profile"
            ),
        }
        self.workspace = Workspace.objects.create(title="test workspace")

        # make the admin_a_deleted_profile user admin of the workspace
        self.admin_a_deleted_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_a_deleted_profile"],
            role=WS_ADMIN,
            deleted=timezone.now(),
        )
        # make the member_a_deleted_profile user member of the workspace
        self.member_a_deleted_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a_deleted_profile"],
            role=WS_MEMBER,
            deleted=timezone.now(),
        )

    def test_deleted_member_is_denied_access_to_list(self):
        """A soft-deleted Profile has no access to the profiles of a workspace."""
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["member_a_deleted_profile"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_member_is_denied_access_to_profile(self):
        """A user with a soft-deleted profile can not retrieve its own profile."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_deleted_profile.short_uuid,
            },
        )

        token = self.users["member_a_deleted_profile"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_member_is_denied_access_to_edit_profile(self):
        """A user with a soft-deleted profile can not edit its own profile.
        When an profile is deleted, this cannot be accessed anymore (404 not found)"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_deleted_profile.short_uuid,
            },
        )

        token = self.users["member_a_deleted_profile"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        with self.subTest("empty payload"):
            response = self.client.patch(url, {}, format="json",)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        with self.subTest("job_title"):
            response = self.client.patch(
                url, {"job_title": "A new title"}, format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_admin_is_denied_access_to_list(self):
        """A soft-deleted admin Profile has no access to the profiles of a workspace."""
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin_a_deleted_profile"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_admin_is_denied_access_to_profile(self):
        """An admin with a soft-deleted profile can not retrieve its own profile.
        When an profile is deleted, this cannot be accessed anymore (404 not found)"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_a_deleted_profile.short_uuid,
            },
        )

        token = self.users["admin_a_deleted_profile"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_admin_is_denied_access_to_edit_profile(self):
        """An admin with a soft-deleted profile can not edit its own profile.
        When an profile is deleted, this cannot be accessed anymore (404 not found)"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_a_deleted_profile.short_uuid,
            },
        )

        token = self.users["admin_a_deleted_profile"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        with self.subTest("empty payload"):
            response = self.client.patch(url, {}, format="json",)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        with self.subTest("job_title"):
            response = self.client.patch(
                url, {"job_title": "A new title"}, format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRemovingProfile(APITestCase):
    def setUp(self):
        self.users = {
            "admin_a": User.objects.create(username="admin_a"),
            "admin_b": User.objects.create(username="admin_b"),
            "member_a": User.objects.create(username="member_a"),
            "member_b": User.objects.create(username="member_b"),
            "user_a": User.objects.create(username="user_a"),
        }
        self.workspace = Workspace.objects.create(title="test workspace")

        # make the admin_a user member of the workspace
        self.admin_a_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_a"],
            role=WS_ADMIN,
        )
        # make the admin_a user member of the workspace
        self.admin_b_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_b"],
            role=WS_ADMIN,
        )
        # make the member_a user member of the workspace
        self.member_a_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
        )
        # make the member_b user member of the workspace
        self.member_b_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_b"],
            role=WS_MEMBER,
        )

    def test_admin_can_remove_profile(self):
        """Admins of a workspace can remove a member from it."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_b_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        before_delete = timezone.now()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertGreater(
            UserProfile.objects.filter(uuid=self.admin_b_profile.uuid).first().deleted,
            before_delete,
        )

    def test_member_cannot_remove_profile(self):
        """Members of a workspace cannot remove a member from it."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["member_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(
            UserProfile.objects.filter(uuid=self.member_a_profile.uuid).first().deleted
        )

    def test_non_member_cannot_remove_profile(self):
        """Non members of a workspace cannot remove profiles from it."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_a_profile.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(
            UserProfile.objects.filter(uuid=self.member_a_profile.uuid).first().deleted
        )

    def test_admin_cannot_remove_profiles_from_other_workspace(self):
        """Removing a profile is limited to workspaces an admin is member of."""
        extra_workspace = Workspace.objects.create(title="extra test workspace")
        extra_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=extra_workspace.uuid,
            user=self.users["user_a"],
            role=WS_MEMBER,
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": extra_workspace.short_uuid,
                "short_uuid": extra_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(
            UserProfile.objects.filter(uuid=extra_profile.uuid).first().deleted
        )

    def test_admin_cannot_remove_self_profile(self):
        """An admin an not remove its own profile from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.admin_a_profile.short_uuid,
            },
        )

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(
            UserProfile.objects.filter(uuid=self.admin_a_profile.uuid).first().deleted
        )

