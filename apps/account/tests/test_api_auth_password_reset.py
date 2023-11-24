import re

import pytest
from django.core import mail
from django.urls import reverse
from rest_framework import status

from account.models.user import PasswordResetLog
from tests import AskAnnaAPITestCase


class BaseAuthPasswordResetAPI(AskAnnaAPITestCase):
    url = reverse("rest_password_reset", kwargs={"version": "v1"})
    status_url = reverse("rest_password_reset_token_status", kwargs={"version": "v1"})

    @pytest.fixture(autouse=True)
    def email_backend_setup(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    @pytest.fixture(autouse=True)
    def _set_users(self, test_users):
        self.users = test_users


class TestResetPasswordAPI(BaseAuthPasswordResetAPI):
    """Testing the reset password function for /auth/password/reset/"""

    def test_reset_existing_account(self):
        """Request a reset for an existing account"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "http://front.end/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        invite_email = mail.outbox[0]
        assert invite_email.subject == "Password reset instructions for your account on AskAnna"
        assert invite_email.to == [self.users["workspace_member"].email]
        assert invite_email.from_email == "AskAnna <support@askanna.io>"
        assert "http://front.end/" in invite_email.body

    def test_reset_existing_account_without_front_end_url(self):
        """Request a reset for an existing account"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        invite_email = mail.outbox[0]
        assert invite_email.subject == "Password reset instructions for your account on AskAnna"
        assert invite_email.to == [self.users["workspace_member"].email]
        assert invite_email.from_email == "AskAnna <support@askanna.io>"

    def test_reset_nonexisting_account(self):
        """Request a reset for an existing account"""
        response = self.client.post(
            self.url,
            {
                "email": "johndoe@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 0

    def test_reset_invalid_email(self):
        """Request a reset for an invalid email"""
        response = self.client.post(
            self.url,
            {
                "email": "invalid@",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(mail.outbox) == 0
        assert response.data["email"] == ["Enter a valid email address."]

    def test_reset_email_empty(self):
        """Request a reset without specifying the email"""
        response = self.client.post(
            self.url,
            {
                "email": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(mail.outbox) == 0
        assert response.data["email"] == ["This field may not be blank."]

    def test_reset_invalid_email_absent(self):
        """Request a reset without specifying the email"""
        response = self.client.post(
            self.url,
            {
                "front_end_url": "http://front.end/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 0)
        self.assertTrue(response.data.get("email") == ["This field is required."])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_existing_account_checklog(self):
        """Request a reset for an existing account and check the password reset log"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "http://front.end.check/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        prl = PasswordResetLog.objects.get(email=self.users["workspace_member"].email)
        assert prl.front_end_domain == "front.end.check"

    def test_reset_existing_account_check_status(self):
        """Request a reset for an existing account and check the status of the resetrequest"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["workspace_member"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["workspace_member"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")
        uid = invite_link.group("uid")

        assert invite_link.group("scheme") == "http"
        assert invite_link.group("domain") == "front.end.statuscheck"

        response = self.client.get(
            self.status_url,
            {
                "token": token,
                "uid": uid,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "valid"

    def test_reset_existing_account_check_status_missing_token(self):
        """Request a reset for an existing account and check the status of the reset request without token"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["workspace_member"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["workspace_member"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        uid = invite_link.group("uid")

        assert invite_link.group("scheme") == "http"
        assert invite_link.group("domain") == "front.end.statuscheck"

        response = self.client.get(
            self.status_url,
            {
                "token": "",
                "uid": uid,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["token"] == ["This field may not be blank."]

    def test_reset_existing_account_check_status_missing_uid(self):
        """Request a reset for an existing account and check the status of the reset request without uid"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["workspace_member"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["workspace_member"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")

        assert invite_link.group("scheme") == "http"
        assert invite_link.group("domain") == "front.end.statuscheck"

        response = self.client.get(
            self.status_url,
            {
                "token": token,
                "uid": "",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["uid"] == ["This field may not be blank."]

    def test_reset_existing_account_check_status_invalid_token(self):
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["workspace_member"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["workspace_member"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        uid = invite_link.group("uid")

        assert invite_link.group("scheme") == "http"
        assert invite_link.group("domain") == "front.end.statuscheck"

        response = self.client.get(
            self.status_url,
            {
                "token": "someinvalidtoken",
                "uid": uid,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"][0] == "The User UID and token combination is invalid."
        assert response.data["status"][0] == "invalid"

    def test_reset_existing_account_check_status_invalid_uid(self):
        response = self.client.post(
            self.url,
            {
                "email": self.users["workspace_member"].email,
                "front_end_url": "https://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(mail.outbox) == 1

        # Check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["workspace_member"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["workspace_member"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")

        assert invite_link.group("scheme") == "https"
        assert invite_link.group("domain") == "front.end.statuscheck"

        response = self.client.get(
            self.status_url,
            {
                "token": token,
                "uid": "someinvaliduid",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["uid"][0] == "User UID value is invalid."
        assert response.data["status"][0] == "invalid"
