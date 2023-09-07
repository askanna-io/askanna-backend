import pytest
from django.urls import reverse
from rest_framework import status

from account.models.user import User
from tests import AskAnnaAPITestCASE


class BaseAccountAPI(AskAnnaAPITestCASE):
    url = reverse("account-list", kwargs={"version": "v1"})

    @pytest.fixture(autouse=True)
    def _set_users(self, test_users):
        self.users = test_users


class TestAccountListAPI(BaseAccountAPI):
    """Testing the list function for the /v1/accounts/"""

    def test_list_accounts_as_superuser(self):
        """We can list user accounts as a superuser user"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_accounts_as_regular_user(self):
        """We should not be able to list user accounts as a regular user (f.e. a workspace admin)"""
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_accounts_anonymous(self):
        """We cannot list user accounts as anonymous user"""
        self.client.credentials()  # type: ignore
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAccountCreateAPI(BaseAccountAPI):
    """Testing the create function for the /v1/accounts/"""

    def test_create_account_as_admin(self):
        """We can create a user account as a superuser user"""
        self.set_authorization(self.users["askanna_super_admin"])

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

    def test_create_account_as_regular_member(self):
        """We should not be able to create a user account as regular user"""
        self.set_authorization(self.users["workspace_admin"])

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
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_account_as_anonymous(self):
        """We can create a user when anonymous (new member signup)"""
        self.client.credentials()  # type: ignore

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
        self.client.credentials()  # type: ignore

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

    def test_create_account_as_anonymous_missing_terms_of_use(self):
        """
        We can create a user account as anonymous (new member signup)
        But we need to accept the terms of use
        """
        self.client.credentials()  # type: ignore

        response = self.client.post(
            self.url,
            {
                "name": "New User Test",
                "email": "anon-test@askanna.dev",
                "password": "1234567890abcdef",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field is required." == response.data["terms_of_use"][0]  # type: ignore

        response = self.client.post(
            self.url,
            {
                "name": "New User Test",
                "email": "anon-test@askanna.dev",
                "password": "1234567890abcdef",
                "terms_of_use": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Please accept the terms of use." == response.data["terms_of_use"][0]  # type: ignore

    def test_create_account_as_anonymous_too_short_password(self):
        """
        We can create a user account as anonymous (new member signup)
        But the password is too short and we get the feedback
        """
        self.client.credentials()  # type: ignore

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


class TestAccountUpdateAPI(BaseAccountAPI):
    """Testing the update function for the /v1/accounts/{suuid}/"""

    _url = None

    @property
    def url(self):
        if self._url is None:
            self._url = reverse(
                "account-detail",
                kwargs={"version": "v1", "suuid": self.users["workspace_member"].suuid},
            )
        return self._url

    def test_update_account_as_admin(self):
        """We cannot update a user account via the API as a superuser user"""
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-user",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_account_as_account_owner(self):
        """We can update a user account on own user account"""
        self.set_authorization(self.users["workspace_member"])

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
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-admin",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_account_as_anonymous(self):
        """A not logged in user cannot update anything"""
        self.client.credentials()  # type: ignore

        response = self.client.patch(
            self.url,
            {
                "email": "new-email@askanna.dev",
                "password": "1234567890abcdef",
                "old_password": "password-admin",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_account_as_user_missing_old_password(self):
        """We can NOT update an user as user on own user account without current password"""
        self.set_authorization(self.users["workspace_member"])

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
        self.set_authorization(self.users["workspace_member"])

        response = self.client.patch(
            self.url,
            {"email": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field may not be blank." == response.data["email"][0]  # type: ignore

    def test_update_account_as_user_with_wrong_password(self):
        """We can update an user as user on own user account, but with wrong password expect error"""
        self.set_authorization(self.users["workspace_member"])

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
