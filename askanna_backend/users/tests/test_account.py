import pytest
from django.urls import reverse
from rest_framework import status
from users.models import User

from .base_tests import BaseAccounts

pytestmark = pytest.mark.django_db


class TestAccountListAPI(BaseAccounts):
    """Testing the list function for the /v1/accounts/"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "account-list",
            kwargs={"version": "v1"},
        )

    def test_list_accounts_as_admin(self):
        """We can list user accounts as an admin user"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_accounts_as_normaluser(self):
        """We should not be able to list user accounts as a normal user"""
        token = self.users["user_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_accounts_anonymous(self):
        """We cannot list user accounts as anonymous user"""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAccountCreateAPI(BaseAccounts):
    """Testing the create function for the /v1/accounts/"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "account-list",
            kwargs={"version": "v1"},
        )

    def test_create_account_as_admin(self):
        """We can create a user account as admin/superuser"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            self.url,
            {
                "name": "Admin Test",
                "email": "admin-test@askanna.dev",
                "password": "1234567890abcdef",
                "terms_of_use": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        User.objects.get(suuid=response.data["suuid"]).delete()  # type: ignore

    def test_create_account_as_normal_member(self):
        """We should not be able to create a user account as normal user"""
        token = self.users["user_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            self.url,
            {
                "name": "User Test",
                "email": "user-test@askanna.dev",
                "password": "1234567890abcdef",
                "terms_of_use": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_account_as_anonymous(self):
        """We can create a user when anonymous (new member signup)"""
        response = self.client.post(
            self.url,
            {
                "name": "New User Test",
                "email": "new-test@askanna.dev",
                "password": "1234567890abcdef",
                "terms_of_use": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        User.objects.get(suuid=response.data["suuid"]).delete()  # type: ignore

    def test_create_account_as_anonymous_email_already_used(self):
        """
        We can create a user account as anonymous (new member signup)
        Here we repeat the signup and will get an error that the e-mail is already used
        """
        response = self.client.post(
            self.url,
            {
                "name": "New User Test",
                "email": "anon-test@askanna.dev",
                "password": "1234567890abcdef",
                "terms_of_use": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        response_2 = self.client.post(
            self.url,
            {
                "name": "New User Test",
                "email": "anon-test@askanna.dev",
                "password": "0123456789abcde",
                "terms_of_use": True,
            },
            format="json",
        )
        assert response_2.status_code == status.HTTP_400_BAD_REQUEST
        assert "This email is already used." == response_2.data["email"][0]  # type: ignore

        User.objects.get(suuid=response.data["suuid"]).delete()  # type: ignore

    def test_create_account_as_anonymous_too_short_password(self):
        """
        We can create a user account as anonymous (new member signup)
        But the password is too short and we get the feedback
        """
        response = self.client.post(
            self.url,
            {
                "name": "New User Test",
                "email": "anon-test@askanna.dev",
                "password": "1234",
                "terms_of_use": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "This password is too short. It must contain at least 10 characters."
            == response.data["password"][0]  # type: ignore
        )


class TestAccountUpdateAPI(BaseAccounts):
    """Testing the update function for the /v1/accounts/{suuid}/"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "account-detail",
            kwargs={"version": "v1", "suuid": self.users["user"].suuid},
        )

    def test_update_account_as_admin(self):
        """We cannot update a user account via the API as admin/superuser"""
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-user",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_account_as_account_owner(self):
        """We can update a user account on own user account"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-user",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_account_as_other_user(self):
        """An other user cannot update a non-owning user account"""
        token = self.users["user_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-admin",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_account_as_anonymous(self):
        """A not logged in user cannot update anything"""
        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-admin",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_account_as_user_missing_old_password(self):
        """We can NOT update an user as user on own user account without current password"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "password": "1234567890abcdef",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "To change your password, you also need to provide the current password."
            == response.data["old_password"][0]  # type: ignore
        )

    def test_update_account_without_email(self):
        """We cannot update an user as user on own user account with blank email"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {"email": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field may not be blank." == response.data["email"][0]  # type: ignore

    def test_update_accouint_as_user_with_wrong_password(self):
        """We can update an user as user on own user account, but with wrong password expect error"""
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "password": "1234567890abcdef",
                "old_password": "password-user-wrong",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "The old password is incorrect." == response.data["old_password"][0]  # type: ignore
