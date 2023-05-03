import re

import pytest
from django.core import mail
from django.urls import reverse
from rest_framework import status

from .base_tests import BaseAccounts
from account.models.user import PasswordResetLog

pytestmark = pytest.mark.django_db


class TestResetPasswordAPI(BaseAccounts):
    """Testing the reset password function for /auth/password/reset/"""

    def setUp(self):
        super().setUp()
        self.url = reverse("rest_password_reset", kwargs={"version": "v1"})
        self.status_url = reverse("rest_password_reset_token_status", kwargs={"version": "v1"})

    @pytest.fixture(autouse=True)
    def email_backend_setup(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    def test_reset_existing_account(self):
        """Request a reset for an existing account"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "http://front.end/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1

        invite_email = mail.outbox[0]
        assert invite_email.subject == "Password reset instructions for your account on AskAnna"
        assert invite_email.to == [self.users["user"].email]
        assert invite_email.from_email == "AskAnna <support@askanna.io>"
        assert "http://front.end/" in invite_email.body
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

    def test_reset_existing_account_without_front_end_url(self):
        """Request a reset for an existing account"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1

        invite_email = mail.outbox[0]
        assert invite_email.subject == "Password reset instructions for your account on AskAnna"
        assert invite_email.to == [self.users["user"].email]
        assert invite_email.from_email == "AskAnna <support@askanna.io>"
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

    def test_reset_nonexisting_account(self):
        """Request a reset for an existing account"""
        response = self.client.post(
            self.url,
            {
                "email": "johndoe@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 0
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

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
        assert response.data["email"] == ["Enter a valid email address."]  # type: ignore

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
        assert response.data["email"] == ["This field may not be blank."]  # type: ignore

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
        self.assertTrue(response.data.get("email") == ["This field is required."])  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_existing_account_checklog(self):
        """Request a reset for an existing account and check the password reset log"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "http://front.end.check/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        assert prl.front_end_domain == "front.end.check"

    def test_reset_existing_account_check_status(self):
        """Request a reset for an existing account and check the status of the resetrequest"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["user"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")  # type: ignore
        uid = invite_link.group("uid")  # type: ignore

        assert invite_link.group("scheme") == "http"  # type: ignore
        assert invite_link.group("domain") == "front.end.statuscheck"  # type: ignore

        response = self.client.get(
            self.status_url,
            {
                "token": token,
                "uid": uid,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "valid"  # type: ignore

    def test_reset_existing_account_check_status_missing_token(self):
        """Request a reset for an existing account and check the status of the reset request without token"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["user"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        uid = invite_link.group("uid")  # type: ignore

        assert invite_link.group("scheme") == "http"  # type: ignore
        assert invite_link.group("domain") == "front.end.statuscheck"  # type: ignore

        response = self.client.get(
            self.status_url,
            {
                "token": "",
                "uid": uid,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["token"] == ["This field may not be blank."]  # type: ignore

    def test_reset_existing_account_check_status_missing_uid(self):
        """Request a reset for an existing account and check the status of the reset request without uid"""
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["user"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")  # type: ignore

        assert invite_link.group("scheme") == "http"  # type: ignore
        assert invite_link.group("domain") == "front.end.statuscheck"  # type: ignore

        response = self.client.get(
            self.status_url,
            {
                "token": token,
                "uid": "",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["uid"] == ["This field may not be blank."]  # type: ignore

    def test_reset_existing_account_check_status_invalid_token(self):
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "http://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["user"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        uid = invite_link.group("uid")  # type: ignore

        assert invite_link.group("scheme") == "http"  # type: ignore
        assert invite_link.group("domain") == "front.end.statuscheck"  # type: ignore

        response = self.client.get(
            self.status_url,
            {
                "token": "someinvalidtoken",
                "uid": uid,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"][0] == "The User UID and token combination is invalid."  # type: ignore
        assert response.data["status"][0] == "invalid"  # type: ignore

    def test_reset_existing_account_check_status_invalid_uid(self):
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_url": "https://front.end.statuscheck/",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert response.data["detail"] == "Password reset request has been processed."  # type: ignore

        # Check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        assert prl.front_end_domain == "front.end.statuscheck"

        invite_email = mail.outbox[0]
        assert invite_email.to == [self.users["user"].email]

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",  # noqa
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")  # type: ignore

        assert invite_link.group("scheme") == "https"  # type: ignore
        assert invite_link.group("domain") == "front.end.statuscheck"  # type: ignore

        response = self.client.get(
            self.status_url,
            {
                "token": token,
                "uid": "someinvaliduid",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["uid"][0] == "User UID value is invalid."  # type: ignore
        assert response.data["status"][0] == "invalid"  # type: ignore
