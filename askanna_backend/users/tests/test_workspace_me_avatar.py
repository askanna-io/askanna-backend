import pytest
from django.urls import reverse
from rest_framework import status

from .base_tests import BaseAvatar

pytestmark = pytest.mark.django_db


class TestWorkspaceMeAvatarAPI(BaseAvatar):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-me-avatar",
            kwargs={
                "version": "v1",
                "suuid": self.workspace_private.suuid,
            },
        )

    def test_update_avatar_as_admin(self):
        """We cannot update avatar as an admin"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.put(
            self.url,
            {"avatar": self.image_base64},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_avatar_as_member(self):
        """We can update avatar as an member as owner"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.put(
            self.url,
            {"avatar": self.image_base64},
            format="json",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_update_avatar_as_anonymous(self):
        """We can NOT update avatar as anonymous"""
        response = self.client.put(
            self.url,
            {"avatar": self.image_base64},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_avatar_as_member_faulty_image(self):
        """We can NOT update avatar as an member when the image is not an image"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.put(
            self.url,
            {"avatar": self.image_base64_invalid},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_avatar_as_member_faulty_image_base64(self):
        """
        We can NOT update avatar as an member when the image is corrupted
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.put(
            self.url,
            {"avatar": self.image_base64[:-5]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_avatar_as_admin(self):
        """We cannot delete avatar as an admin"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_avatar_as_member(self):
        """We can delete avatar as an the member"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_avatar_as_anonymous(self):
        """We cannot delete avatars if not logged in"""
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
