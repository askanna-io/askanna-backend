import pytest
from django.urls import reverse
from rest_framework import status

from .base_tests import BaseWorkspace

pytestmark = pytest.mark.django_db


class BaseWorkspaceMe(BaseWorkspace):
    def setUp(self):
        super().setUp()
        self.url_private = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "suuid": self.workspace_private.suuid,
            },
        )
        self.url_public = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "suuid": self.workspace_public.suuid,
            },
        )
        self.url_non_existing = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "suuid": self.workspace_private.suuid[:-1] + "1",
            },
        )


class TestWorkspaceMeGet(BaseWorkspaceMe):
    def test_me_as_admin(self):
        """An AskAnna admin doesn't have acces to the workspace"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_me_as_workspace_admin(self):
        """A workspace admin can get /me on a private workspace"""
        token = self.users["workspace_admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.remove"] is True  # type: ignore

    def test_me_as_workspace_member(self):
        """A workspace member can get /me on a private workspace"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.remove"] is False  # type: ignore

    def test_me_as_user_public_workspace(self):
        """A user can get /me on a public workspace"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.remove"] is False  # type: ignore

    def test_me_as_user_non_existing_workspace(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url_non_existing)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_me_as_anonymous_private_workspace(self):
        """An anonymous user cannot get /me on a private workspace"""
        response = self.client.get(self.url_private)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_as_anonymous_public_workspace(self):
        """An anonymous user can get /me on a public workspace"""
        response = self.client.get(self.url_public)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"]["workspace.me.view"] is True  # type: ignore


class TestWorkspaceMeDelete(BaseWorkspaceMe):
    def test_me_as_admin(self):
        """Anna is not a member and not admin, so not allowed to delete the non-existing workspace membership"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_me_as_anonymous(self):
        """Anonymous cannot delete /me"""
        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_as_member_delete_user_copies_global_profile_data_to_membership(self):
        """
        On deleting a user via /workspace/{suuid}/me/ we should update the UserProfile
        This test is 2 sided:
        - delete the workspace membership via /workspace/{suuid}/me/
        - check the membership profile in database (refresh object first)
        """
        self.member_profile.refresh_from_db()
        assert self.member_profile.name == "name of member in membership"
        assert self.member_profile.job_title == "job_title of member in membership"

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Reload the details of the membership
        self.member_profile.refresh_from_db()
        assert self.member_profile.deleted is not None

        # The following values are coming from the global user and should be copied to membership
        assert self.member_profile.name == "user"
        assert self.member_profile.job_title == ""

        # The following values are set on creating the UserProfile/Membership and should not found in the
        # member_profile anymore
        assert self.member_profile.name != "name of member in membership"
        assert self.member_profile.job_title != "job_title of member in membership"

    def test_me_as_member_delete_membership_NO_copy_global_profile_to_membership(self):
        """
        Deleting membership but NOT using use_global_profile
        """
        self.member_profile_b.refresh_from_db()
        assert self.member_profile_b.name == "name of member_b in membership"
        assert self.member_profile_b.job_title == "job_title of member_b in membership"

        token = self.users["user_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(self.url_private)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Reload the details of the membership
        self.member_profile_b.refresh_from_db()

        # The following values are coming from the global user profile and should not be found here
        assert self.member_profile_b.name != "user_b"
        assert self.member_profile_b.job_title != "Job Title user_b"

        # The following values are set on creating the UserProfile/Membership and should still be found in the
        # member_profile
        assert self.member_profile_b.name == "name of member_b in membership"
        assert self.member_profile_b.job_title == "job_title of member_b in membership"


class TestWorkspaceMePatch(BaseWorkspaceMe):
    def test_me_as_admin(self):
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.patch(
            self.url_private,
            {
                "use_global_profile": True,
                "name": "some random name that is not used",
                "job_title": "some random job_title that is not used",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_patch_use_global_profile(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

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
        assert response.data.get("name") != "some random name that is not used"  # type: ignore
        assert response.data.get("job_title") != "some random job_title that is not used"  # type: ignore
        assert response.data.get("name") == "user"  # type: ignore
        assert response.data.get("job_title") == ""  # type: ignore
        assert response.data.get("use_global_profile") is True  # type: ignore

        # How do I look like? Do another get on the workspace/me.
        response_get = self.client.get(self.url_private)
        assert response_get.status_code == status.HTTP_200_OK

        # Name and job_title are coming from the global profile
        assert response.data.get("name") != "some random name that is not used"  # type: ignore
        assert response.data.get("job_title") != "some random job_title that is not used"  # type: ignore
        assert response.data.get("name") == "user"  # type: ignore
        assert response.data.get("job_title") == ""  # type: ignore
        assert response.data.get("use_global_profile") is True  # type: ignore

    def test_member_patch_not_use_global_profile(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

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

        # The fields stored in membership itself, but not reflected in effective name because
        # use_global_profile is True
        assert response.data.get("name") == "some random name that is used"  # type: ignore
        assert response.data.get("job_title") == "some random job_title that is used"  # type: ignore
        assert response.data.get("name") != "user"  # type: ignore
        assert response.data.get("job_title") != ""  # type: ignore
        assert response.data.get("use_global_profile") is False  # type: ignore

        # How do I look like? Do another get on the workspace/me.
        response_get = self.client.get(self.url_private)
        assert response_get.status_code == status.HTTP_200_OK

        # Name and job_title are coming from the global profile
        assert response.data.get("name") == "some random name that is used"  # type: ignore
        assert response.data.get("job_title") == "some random job_title that is used"  # type: ignore
        assert response.data.get("name") != "user"  # type: ignore
        assert response.data.get("job_title") != ""  # type: ignore
        assert response.data.get("use_global_profile") is False  # type: ignore

    def test_me_as_anonymous(self):
        response = self.client.patch(
            self.url_private,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
