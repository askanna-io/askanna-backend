import pytest
from django.urls import reverse
from rest_framework import status

from account.models.membership import MSP_WORKSPACE, Membership
from core.permissions.roles import WorkspaceAdmin, WorkspaceMember
from tests import AskAnnaAPITestCase
from workspace.models import Workspace


class BaseWorkspacePeopleAPI(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_workspaces, test_memberships, avatar_file):
        self.users = test_users
        self.workspaces = test_workspaces
        self.memberships = test_memberships
        self.avatar_file = avatar_file


class TestWorkspacePeopleListAPI(BaseWorkspacePeopleAPI):
    def setUp(self):
        super().setUp()
        self.private_url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
            },
        )
        self.public_url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_public"].suuid,
            },
        )

    def test_list_as_superuser(self):
        """A superuser user can NOT list people from a workspace where user is not a member."""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.private_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_as_workspace_admin(self):
        """A workspace admin can list people from a workspace."""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.private_url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_as_workspace_member(self):
        """A workspace member can list people from a workspace."""
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.private_url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_as_non_workspace_member(self):
        """A non workspace member can NOT list people from a workspace."""
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.private_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = self.client.get(self.public_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_as_anonymous(self):
        """Anonymous users can not list people from a workspace."""
        self.client.credentials()

        response = self.client.get(self.private_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = self.client.get(self.public_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestWorkspacePeopleDetailAPI(BaseWorkspacePeopleAPI):
    def test_retrieve_profile_requires_correct_workspace(self):
        """The path to a profile requires the correct parrent be given."""
        workspace_to_fail = Workspace.objects.create(
            name="workspace to fail", created_by_user=self.users["workspace_admin"]
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": workspace_to_fail.suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        workspace_to_fail.delete()

    def test_retrieve_profile_as_superuser_fails(self):
        """A superuser user can NOT see profiles from a workspace where user is not a member."""
        self.set_authorization(self.users["askanna_super_admin"])

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_profile_as_non_member_fails(self):
        """Non members can not see profiles from a workspace."""
        self.set_authorization(self.users["no_workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_profile_as_anonymous_fails(self):
        """Anonymous users can not see profiles from a workspace."""
        self.client.credentials()
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_profile_as_member(self):
        """A member can see existing profiles from a workspace."""
        self.set_authorization(self.users["workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert {"suuid": self.memberships["workspace_private_admin"].suuid}.items() <= dict(response.data).items()

    def test_retrieve_profile_as_admin(self):
        """An admin can see existing profiles from a workspace."""
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert {"suuid": self.memberships["workspace_private_member"].suuid}.items() <= dict(response.data).items()

    def test_retrieve_profile_avatar_as_member(self):
        """A member can get existing profile avatars from a private workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        self.set_authorization(self.users["workspace_admin"])
        self.client.patch(
            url,
            {"avatar": self.avatar_file},
            format="multipart",
        )

        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert response.data["avatar_file"] is not None
        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        self.client.patch(url, {"avatar": ""}, format="multipart")

    def test_verify_member_cannot_access_avatar_file_when_use_global_profile(self):
        """A member cannot get the avatar file of a membership profile if the profile uses the global profile."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(
            url,
            {"avatar": self.avatar_file},
            format="multipart",
        )
        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.set_authorization(self.users["workspace_admin"])
        self.client.patch(
            reverse(
                "workspace-me",
                kwargs={
                    "version": "v1",
                    "suuid": self.workspaces["workspace_private"].suuid,
                },
            ),
            {"use_global_profile": True},
            format="json",
        )

        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Verify that "original" avatar URL cannot be accessed by member
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        self.set_authorization(self.users["workspace_admin"])
        self.client.patch(url, {"avatar": ""}, format="multipart")

    def test_retrieve_profile_avatar_as_anonymous_for_private_workspace_fails(self):
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        self.client.credentials()
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(
            url,
            {"avatar": self.avatar_file},
            format="multipart",
        )
        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.client.credentials()
        # Anonymous user cannot access membership profile info
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        self.set_authorization(self.users["workspace_admin"])
        self.client.patch(url, {"avatar": ""}, format="multipart")

    def test_retrieve_profile_avatar_as_anonymous_for_public_workspace(self):
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_public"].suuid,
                "suuid": self.memberships["workspace_public_admin"].suuid,
            },
        )

        self.client.credentials()
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(
            url,
            {"avatar": self.avatar_file},
            format="multipart",
        )
        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.client.credentials()
        # Anonymous user cannot access membership profile info
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # ...but can access avatar file of membership profile (a.o. used for showing avatar on run page)
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        self.client.patch(url, {"avatar": ""}, format="multipart")


class TestWorkspacePeopleUpdateAPI(BaseWorkspacePeopleAPI):
    def test_superuser_can_not_change_member_profile(self):
        """A profile can not be changed by a superuser if the user is not an admin of the workspace."""
        self.set_authorization(self.users["askanna_super_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        response = self.client.patch(url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_member_can_not_change_other_member_profile(self):
        """A profile can not be changed by another member"""
        self.set_authorization(self.users["workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        response = self.client.patch(url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_is_restricted_to_correct_workspace(self):
        """An admin in one workspace is not an admin in another."""
        new_workspace = Workspace.objects.create(name="test workspace", created_by_user=self.users["workspace_member"])
        new_profile = Membership.objects.get(
            object_type=MSP_WORKSPACE, object_uuid=new_workspace.uuid, user=self.users["workspace_member"]
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": new_workspace.suuid,
                "suuid": new_profile.suuid,
            },
        )

        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            url,
            {"role_code": WorkspaceAdmin.code},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        new_profile.delete()
        new_workspace.delete()

    def test_member_can_change_own_info(self):
        """The job_title field of a member can be changed by the member itself."""
        self.set_authorization(self.users["workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["job_title"] == "a new job title"

    def test_member_can_change_own_avatar(self):
        self.set_authorization(self.users["workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )
        response = self.client.get(url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["avatar_file"] is None

        response = self.client.patch(
            url,
            {"avatar": self.avatar_file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["avatar_file"] is not None

        avatar_file = response.data["avatar_file"]
        assert isinstance(avatar_file, dict)
        assert avatar_file.get("type") is not None
        assert avatar_file.get("url") is not None

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        response = self.client.patch(
            url,
            {"avatar": ""},
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["avatar_file"] is None

        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_change_other_member_info(self):
        """The job_title field can be changed by an admin."""
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["job_title"] == "a new job title"

    def test_admin_can_change_own_info(self):
        """The job_title of an admin can be changed by the admin itself."""
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        response = self.client.patch(
            url,
            {"job_title": "a new job title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["job_title"] == "a new job title"

    def test_admin_can_change_member_role(self):
        """An admin can change the profile of a member to admin."""
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.patch(
            url,
            {"role_code": WorkspaceAdmin.code},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["code"] == WorkspaceAdmin.code
        assert Membership.objects.get(pk=self.memberships["workspace_private_member"].pk).role == WorkspaceAdmin.code

        response = self.client.patch(
            url,
            {"role_code": WorkspaceMember.code},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["code"] == WorkspaceMember.code
        assert Membership.objects.get(pk=self.memberships["workspace_private_member"].pk).role == WorkspaceMember.code

    def test_change_admin_role_by_self_fails(self):
        """An admin can not itself change its role."""
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        response = self.client.patch(
            url,
            {"role_code": WorkspaceMember.code},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestWorkspacePeopleDeleteAPI(BaseWorkspacePeopleAPI):
    def test_delete_member_with_test_access_to_list_is_denied(self):
        """
        A workspace admin can delete a workspace member and as per direct the member will not have access to the
        workspace anymore.
        """
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_member_admin_can_not_delete_itself(self):
        """A workspace admin can not delete it's own profile"""
        self.set_authorization(self.users["workspace_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_admin"].suuid,
            },
        )

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_member_cannot_remove_profile(self):
        """Members of a workspace cannot remove a member from it."""
        self.set_authorization(self.users["workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Membership.objects.get(uuid=self.memberships["workspace_private_member"].uuid).deleted_at is None

    def test_superusers_cannot_remove_profile(self):
        """Superusers that are not a member of a workspace cannot remove profiles from it."""
        self.set_authorization(self.users["askanna_super_admin"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Membership.objects.get(uuid=self.memberships["workspace_private_member"].uuid).deleted_at is None

    def test_non_member_cannot_remove_profile(self):
        """Non members of a workspace cannot remove profiles from it."""
        self.set_authorization(self.users["no_workspace_member"])
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Membership.objects.get(uuid=self.memberships["workspace_private_member"].uuid).deleted_at is None

    def test_anonymous_cannot_remove_profile(self):
        """An anonymous request cannot remove profiles from it."""
        self.client.credentials()
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspaces["workspace_private"].suuid,
                "suuid": self.memberships["workspace_private_member"].suuid,
            },
        )

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Membership.objects.get(uuid=self.memberships["workspace_private_member"].uuid).deleted_at is None
