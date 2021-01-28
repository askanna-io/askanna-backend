from django.urls import reverse
import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from .base_tests import BaseUsers

pytestmark = pytest.mark.django_db


class TestUserListAPI(BaseUsers, APITestCase):
    """
    Testing the list function for the /v1/accounts/
    """

    def setUp(self):
        self.url = reverse("user-list", kwargs={"version": "v1"},)

    def test_list_users_as_admin(self):
        """
        We can list users as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_as_normaluser(self):
        """
        We should not be able to list users as a normal user
        """
        token = self.users["userB"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_anonymous(self):
        """
        We cannot list users as anonymous user
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestUserCreateAPI(BaseUsers, APITestCase):
    """
    Testing the create function for the /v1/accounts/
    """

    def setUp(self):
        self.url = reverse("user-list", kwargs={"version": "v1"},)

    def test_create_user_as_admin(self):
        """
        We can create an user as admin/superuser
        """

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "admin-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "workspace": "my-admin-workspace",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cleanup via internal functions
        User.objects.get(short_uuid=response.data["short_uuid"]).delete()

    def test_create_user_as_normaluser(self):
        """
        We should not be able to create an user as normal user
        """
        # FIXME: should check the business rule for this particular test
        token = self.users["userB"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "user-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "workspace": "my-member-workspace",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_as_anonymous(self):
        """
        We can create an user as anonymous (new member signup)
        """
        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "anon-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "workspace": "my-use-workspace",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cleanup via internal functions
        User.objects.get(short_uuid=response.data["short_uuid"]).delete()

    def test_create_user_as_anonymous_without_workspace(self):
        """
        We can create an user as anonymous (new member signup)
        But not specifying the workspace
        """
        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "anon-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cleanup via internal functions
        User.objects.get(short_uuid=response.data["short_uuid"]).delete()

    def test_create_user_as_anonymous_email_already_used(self):
        """
        We can create an user as anonymous (new member signup)
        Here we repeat the signup and will get an error that the e-mail is already used
        """
        response = self.client.post(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "anon-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(
            self.url,
            {
                "password": "0123456789abcde",
                "email": "anon-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        print(response2.data)
        self.assertIn(
            "This email is already used.", response2.data.get("email"),
        )

        # cleanup via internal functions
        User.objects.get(short_uuid=response.data["short_uuid"]).delete()

    def test_create_user_as_anonymous_too_short_password(self):
        """
        We can create an user as anonymous (new member signup)
        But the password is too short and we get the feedback
        """
        response = self.client.post(
            self.url,
            {
                "password": "1234",
                "email": "anon-test@askanna.dev",
                "front_end_domain": "https://front-end.domain/",
                "terms_of_use": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "The password should be longer than 10 characters.",
            response.data.get("password"),
        )


class TestUserUpdateAPI(BaseUsers, APITestCase):
    """
    Testing the update function for the /v1/accounts/{short_uuid}
    """

    def setUp(self):
        self.url = reverse(
            "user-detail",
            kwargs={"version": "v1", "short_uuid": self.users["user"].short_uuid},
        )

    def test_update_user_as_admin(self):
        """
        We can update an user as admin/superuser
        """

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "new-email@askanna.dev",
                "old_password": "password-user",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_as_user(self):
        """
        We can update an user as user on own user account
        """

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "new-email@askanna.dev",
                "old_password": "password-user",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_as_other_user(self):
        """
        An other user cannot update a non-owning user account
        """

        token = self.users["userB"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "new-email@askanna.dev",
                "old_password": "password-admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_as_anonymous(self):
        """
        A not logged in user cannot update anything
        """

        response = self.client.patch(
            self.url,
            {
                "password": "1234567890abcdef",
                "email": "new-email@askanna.dev",
                "old_password": "password-admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_as_user_missing_old_password(self):
        """
        We can NOT update an user as user on own user account without current password
        """

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {"password": "1234567890abcdef", "email": "new-email@askanna.dev"},
            format="json",
        )
        self.assertIn(
            "To change your password, you also need to provide the current password.",
            str(response.content),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_as_user_emailblank(self):
        """
        We can NOT update an user as user on own user account with blank email
        """

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(self.url, {"email": ""}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address.", str(response.content))

    def test_update_user_as_user_wrong_password(self):
        """
        We can update an user as user on own user account, but with wrong password
        expect error
        """

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {"password": "1234567890abcdef", "old_password": "password-user-wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("The current password is incorrect.", str(response.content))
