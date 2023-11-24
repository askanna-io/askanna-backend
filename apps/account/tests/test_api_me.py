import pytest
from django.urls import reverse
from rest_framework import status

from tests import AskAnnaAPITestCase


class BaseMeAPI(AskAnnaAPITestCase):
    url = reverse("me", kwargs={"version": "v1"})

    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_memberships, avatar_file):
        self.users = test_users
        self.memberships = test_memberships
        self.avatar_file = avatar_file


class TestMeGet(BaseMeAPI):
    """Test to retrieve `/v1/me/`"""

    def test_me_as_superuser(self):
        """A supuser user gets a "me" profile with permission askanna.admin set to True"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is True
        assert permissions.get("askanna.member") is True

    def test_me_as_regular_user(self):
        """As regular user we get a "me" profile with permission askanna.admin set to False"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_deleted_regular_user(self):
        """As regular user we get a "me" profile with permission askanna.admin set to False"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        self.users["workspace_admin"].to_deleted()
        self.users["workspace_admin"].save()
        assert self.users["workspace_admin"].is_active is False

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_as_anonymous(self):
        """As anonymous user we also get a "me" profile"""
        self.client.credentials()

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is False

    def test_me_getting_my_avatar(self):
        """Regular user can get /me and avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url, {"avatar": ""})

    def test_getting_public_avatar_as_anonymous(self):
        """Anonymous requester can get public avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.memberships["workspace_public_admin"].use_global_profile = True
        self.memberships["workspace_public_admin"].save()

        self.client.credentials()
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url, {"avatar": ""})

    def test_getting_public_avatar_as_non_workspace_member(self):
        """Non workspace member can get public avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.memberships["workspace_public_admin"].use_global_profile = True
        self.memberships["workspace_public_admin"].save()

        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url, {"avatar": ""})

    def test_getting_private_avatar_as_anonymouse_not_allowed(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.memberships["workspace_public_admin"].use_global_profile = False
        self.memberships["workspace_public_admin"].save()

        self.client.credentials()
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url, {"avatar": ""})

    def test_getting_private_avatar_as_non_workspace_member_not_allowed(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.memberships["workspace_public_admin"].use_global_profile = False
        self.memberships["workspace_public_admin"].save()

        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url, {"avatar": ""})

    def test_getting_private_avatar_as_workspace_member_allowed(self):
        """Regular user can get /me and avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "avatar": self.avatar_file,
            },
            format="multipart",
        )

        avatar_url = response.data.get("avatar_file").get("url")
        assert avatar_url is not None

        self.memberships["workspace_public_admin"].use_global_profile = False
        self.memberships["workspace_public_admin"].save()

        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.set_authorization(self.users["workspace_admin"])
        response = self.client.patch(self.url, {"avatar": ""})


class TestMePatch(BaseMeAPI):
    """Test to update AskAnna user profile via `/v1/me/`"""

    def test_me_as_superuser(self):
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "new name"
        assert response.data["job_title"] == "new title"

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is True
        assert permissions.get("askanna.member") is True

    def test_me_as_regular_user(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "new name"
        assert response.data["job_title"] == "new title"

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_regular_user_partial_only_change_name(self):
        """Regular user can update /me with only name"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "name": "new partial name",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "new partial name"

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_regular_user_partial_only_change_job_title(self):
        """Regular user can update /me with only job_title"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "job_title": "new partial title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["job_title"] == "new partial title"

        permissions = response.data["permission"]
        assert isinstance(permissions, dict)
        assert permissions.get("askanna.me") is True
        assert permissions.get("askanna.admin") is False
        assert permissions.get("askanna.member") is True

    def test_me_as_regular_user_to_update_avatar(self):
        """Regular user can update /me with avatar"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
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

        avatar_url = avatar_file.get("url")
        assert avatar_url is not None
        response = self.client.get(avatar_url)
        assert response.status_code == status.HTTP_200_OK

        self.client.patch(self.url, {"avatar": ""}, format="multipart")

    def test_me_as_anonymous(self):
        """Anonymous cannot update /me"""
        self.client.credentials()

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "job_title": "new title",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMeDelete(BaseMeAPI):
    """Test to delete user account via /v1/me/"""

    def test_me_as_superuser(self):
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_me_as_regular_user(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_me_as_anonymous(self):
        """Anonymous cannot delete /me"""
        self.client.credentials()

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
