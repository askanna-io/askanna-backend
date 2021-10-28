"""Define tests for API of updating user profile image."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

pytestmark = pytest.mark.django_db


class BaseTestAvatarAPI:
    def setUp(self):
        super().setUp()
        self.users = {
            "anna": User.objects.create(
                username="anna",
                email="anna@askanna.io",
                is_staff=True,
                is_superuser=True,
            ),
            "admin": User.objects.create(username="admin", email="admin@example.com"),
            "user": User.objects.create(username="user", email="user@example.com"),
            "user_b": User.objects.create(
                username="user_b",
                email="user_b@askanna.dev",
                name="user_b",
                job_title="Job Title user_b",
            ),
        }
        self.url = reverse(
            "global-me-avatar",
            kwargs={
                "version": "v1",
            },
        )

        self.image_base64_invalid = (
            "data:image/png;base64,c29tZS1pbnZhbGlkLWltYWdlLXN0cmluZw=="
        )

        self.image_base64 = "data:image/png;base64,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"  # noqa:E501

    def tearDown(self):
        for user in self.users.values():
            user.delete()

    def test_update_avatar_as_anna(self):
        """
        We can update avatar as anna
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"avatar": self.image_base64}
        response = self.client.patch(
            self.url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_avatar_as_admin(self):
        """
        We can update avatar as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"avatar": self.image_base64}
        response = self.client.patch(
            self.url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_avatar_as_member(self):
        """
        We can update avatar as an member as owner
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"avatar": self.image_base64}
        response = self.client.patch(
            self.url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_avatar_as_anonymous(self):
        """
        We can NOT update avatar as anonymous
        """
        payload = {"avatar": self.image_base64}
        response = self.client.patch(
            self.url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_avatar_as_member_faulty_image(self):
        """
        We can NOT update avatar as an member when the image is not an image
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"avatar": self.image_base64_invalid}
        response = self.client.patch(
            self.url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_avatar_as_member_faulty_image_base64(self):
        """
        We can NOT update avatar as an member when the image is corrupted
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"avatar": self.image_base64[:-5]}
        response = self.client.patch(
            self.url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_avatar_as_admin(self):
        """
        We can delete avatar as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_avatar_as_member(self):
        """
        We can delete avatar as an the member (owning the profile)
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_avatar_as_anonymous(self):
        """
        We cannot delete avatars if not logged in
        """
        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAvatarAPI(BaseTestAvatarAPI, APITestCase):
    ...
