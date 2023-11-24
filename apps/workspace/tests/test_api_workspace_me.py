import pytest
from django.urls import reverse
from rest_framework import status

from core.utils.suuid import create_suuid
from tests import AskAnnaAPITestCase


class BaseWorkspaceMeAPI(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_workspaces, test_memberships, avatar_file):
        self.users = test_users
        self.workspaces = test_workspaces
        self.memberships = test_memberships
        self.avatar_file = avatar_file

    def setUp(self):
        super().setUp()
        self.url_private = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "suuid": self.workspaces["workspace_private"].suuid,
            },
        )
        self.url_public = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "suuid": self.workspaces["workspace_public"].suuid,
            },
        )
        self.url_non_existing = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "suuid": create_suuid(),
            },
        )


class TestWorkspaceMeGet(BaseWorkspaceMeAPI):
    def test_me_as_superuser(self):
        """A superuser user doesn't have acces to the workspace"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_workspace_admin(self):
        """A workspace admin can get /me on a private workspace where user is a member"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.remove"] is True

    def test_me_as_workspace_member(self):
        """A workspace member can get /me on a private workspace where user is a member"""
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.remove"] is False
        assert response.data["permission"]["workspace.people.invite.create"] is True

    def test_me_as_non_workspace_member_for_private_workspace(self):
        """A non workspace member can NOT get /me on a private workspace where user is not a member"""
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_non_workspace_member_for_public_workspace(self):
        """A non workspace member can get /me on a public workspace"""
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.me.view"] is True
        assert response.data["permission"]["workspace.remove"] is False

    def test_me_as_user_non_existing_workspace(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url_non_existing)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_anonymous_private_workspace(self):
        """An anonymous user cannot get /me on a private workspace"""
        self.client.credentials()

        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_as_anonymous_public_workspace(self):
        """An anonymous user can get /me on a public workspace"""
        self.client.credentials()

        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.me.view"] is True
        assert response.data["permission"]["workspace.remove"] is False

    def test_me_getting_my_membership_avatar(self):
        """Regular user can update /me with avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url_private,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.client.patch(self.url_private, {"avatar": ""}, format="multipart")

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url_public, {"avatar": ""})

    def test_getting_public_avatar_as_anonymous(self):
        """Anonymous requester can get public avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url_public,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.client.credentials()
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url_public, {"avatar": ""})

    def test_getting_public_avatar_as_non_workspace_member(self):
        """Non workspace member can get public avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url_public,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url_public, {"avatar": ""})

    def test_getting_private_avatar_as_anonymouse_not_allowed(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url_private,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.client.credentials()
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url_private, {"avatar": ""})

    def test_getting_private_avatar_as_non_workspace_member_not_allowed(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url_private,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url_private, {"avatar": ""})

    def test_getting_private_avatar_as_workspace_member_allowed(self):
        """Regular user can get /me and avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url_private,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url_private, {"avatar": ""})


class TestWorkspaceMePatch(BaseWorkspaceMeAPI):
    def test_me_as_superuser(self):
        """A superuser is not a member and not a workspace admin, so cannot patch workspace membership"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.patch(
            self.url_private,
            {
                "use_global_profile": True,
                "name": "some random name that is not used",
                "job_title": "some random job_title that is not used",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_member_patch_use_global_profile(self):
        """A workspace member can patch /me on a private workspace where user is a member"""
        self.set_authorization(self.users["workspace_member"])

        response = self.client.patch(
            self.url_private,
            {
                "use_global_profile": True,
                "name": "some random name that is not used",
                "job_title": "some random job_title that is not used",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # The fields stored in membership itself, but not reflected in effective name because
        # use_global_profile is True
        assert response.data.get("name") != "some random name that is not used"
        assert response.data.get("job_title") != "some random job_title that is not used"
        assert response.data.get("name") == "workspace member"
        assert response.data.get("job_title") == ""
        assert response.data.get("use_global_profile") is True

    def test_member_patch_not_use_global_profile(self):
        """A workspace member can patch /me on a private workspace where user is a member"""
        self.set_authorization(self.users["workspace_member"])

        response = self.client.patch(
            self.url_private,
            {
                "use_global_profile": False,
                "name": "some random name that is used",
                "job_title": "some random job_title that is used",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # The fields stored in membership itself, and reflected in effective name because
        # use_global_profile is False
        assert response.data.get("name") == "some random name that is used"
        assert response.data.get("job_title") == "some random job_title that is used"
        assert response.data.get("use_global_profile") is False

    def test_member_patch_avatar(self):
        """A workspace member can patch /me to update avatar on a private workspace where user is a member"""
        self.set_authorization(self.users["workspace_member"])

        response = self.client.patch(
            self.url_private,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["avatar_file"] is not None

        avatar_file = response.data["avatar_file"]
        assert isinstance(avatar_file, dict)
        assert avatar_file.get("type") is not None
        assert avatar_file.get("url") is not None

        self.client.patch(self.url_private, {"avatar": ""}, format="multipart")

    def test_me_as_anonymous(self):
        """Anonymous cannot patch workspace /me"""
        self.client.credentials()

        response = self.client.patch(
            self.url_private,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestWorkspaceMeDelete(BaseWorkspaceMeAPI):
    def test_me_as_superuser(self):
        """A superuser is not a member and not a workspace admin, so cannot delete workspace membership"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_member_delete_user_copies_global_profile_data_to_membership(self):
        """
        On deleting a user via /workspace/{suuid}/me/ we should update the Membership
        This test is 2 sided:
        - delete the workspace membership via /workspace/{suuid}/me/
        - check the membership profile in database (refresh object first)
        """
        membership = self.memberships["workspace_private_admin"]
        assert membership.deleted_at is None
        assert membership.name == "workspace private admin"
        assert membership.job_title == "job_title of workspace private admin"

        self.set_authorization(self.users["workspace_admin"])

        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Reload the details of the membership
        membership.refresh_from_db()
        assert membership.deleted_at is not None

        # The following values are coming from the global user and should be copied to membership
        assert membership.name == "workspace admin"
        assert membership.job_title == ""

    def test_me_as_member_delete_membership_no_copy_global_profile_to_membership(self):
        """
        Deleting membership but NOT using use_global_profile
        """
        membership = self.memberships["workspace_private_member"]
        assert membership.deleted_at is None
        assert membership.name == "workspace private member"
        assert membership.job_title == "job_title of workspace private member"

        self.set_authorization(self.users["workspace_member"])

        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Reload the details of the membership
        membership.refresh_from_db()
        assert membership.deleted_at is not None

        # The following values should not be changed because use_global_profile is False
        assert membership.name == "workspace private member"
        assert membership.job_title == "job_title of workspace private member"

    def test_me_as_anonymous(self):
        """Anonymous cannot delete workspace /me"""
        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
