import re

from django.urls import reverse
import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from workspace.models import Workspace
from workspace.views import PersonViewSet
from users.models import User, PasswordResetLog
from .base_tests import BaseUsers

pytestmark = pytest.mark.django_db
from django.core import mail


class TestResetPasswordAPI(BaseUsers, APITestCase):
    """
    Testing the reset password function for /rest-auth/password/reset/
    """

    def setUp(self):
        self.url = reverse("rest_password_reset")
        self.status_url = reverse("token-status")

    @pytest.fixture(autouse=True)
    def email_backend_setup(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    def test_reset_existing_account(self):
        """
        Request a reset for an existing account
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(
            invite_email.subject, "Password reset instructions for your account on AskAnna"
        )
        self.assertEqual(invite_email.to, [self.users["user"].email])
        self.assertEqual(invite_email.from_email, "AskAnna <support@askanna.io>")
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_existing_account_without_front_end_domain(self):
        """
        Request a reset for an existing account
        """
        response = self.client.post(
            self.url, {"email": self.users["user"].email,}, format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(
            invite_email.subject, "Password reset instructions for your account on AskAnna"
        )
        self.assertEqual(invite_email.to, [self.users["user"].email])
        self.assertEqual(invite_email.from_email, "AskAnna <support@askanna.io>")
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_nonexisting_account(self):
        """
        Request a reset for an existing account
        """
        response = self.client.post(
            self.url,
            {"email": "johndoe@askanna.space", "front_end_domain": "http://front.end/"},
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 0)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_invalid_email(self):
        """
        Request a reset for an invalid email
        """
        response = self.client.post(
            self.url,
            {"email": "invalid@", "front_end_domain": "http://front.end/"},
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 0)
        self.assertTrue(response.data.get("email") == ["Enter a valid email address."])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_invalid_email_empty(self):
        """
        Request a reset without specifying the email
        Expect a bad request
        """
        response = self.client.post(
            self.url,
            {"email": "", "front_end_domain": "http://front.end/"},
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 0)
        self.assertTrue(response.data.get("email") == ["This field may not be blank."])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_invalid_email_absent(self):
        """
        Request a reset without specifying the email
        Expect a bad request
        """
        response = self.client.post(
            self.url, {"front_end_domain": "http://front.end/"}, format="json",
        )

        self.assertTrue(len(mail.outbox) == 0)
        self.assertTrue(response.data.get("email") == ["This field is required."])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_existing_account_checklog(self):
        """
        Request a reset for an existing account and check the password reset log
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end.check/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        self.assertEqual(prl.front_end_domain, "front.end.check")

    def test_reset_existing_account_check_status(self):
        """
        Request a reset for an existing account and check the status of the resetrequest
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end.statuscheck/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        self.assertEqual(prl.front_end_domain, "front.end.statuscheck")

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(invite_email.to, [self.users["user"].email])

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")
        uid = invite_link.group("uid")

        self.assertEqual(invite_link.group("scheme"), "http")
        self.assertEqual(invite_link.group("domain"), "front.end.statuscheck")

        response = self.client.get(self.status_url, {"token": token, "uid": uid,},)
        print(response.content)

        self.assertTrue(response.data.get("status") == "valid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_existing_account_check_status_incomplete_token(self):
        """
        Request a reset for an existing account and check the status of the resetrequest
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end.statuscheck/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        self.assertEqual(prl.front_end_domain, "front.end.statuscheck")

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(invite_email.to, [self.users["user"].email])

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")
        uid = invite_link.group("uid")

        self.assertEqual(invite_link.group("scheme"), "http")
        self.assertEqual(invite_link.group("domain"), "front.end.statuscheck")

        response = self.client.get(self.status_url, {"token": "", "uid": uid,},)

        self.assertTrue(response.data.get("token") == ["This field may not be blank."])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_existing_account_check_status_incomplete_uid(self):
        """
        Request a reset for an existing account and check the status of the resetrequest
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end.statuscheck/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        self.assertEqual(prl.front_end_domain, "front.end.statuscheck")

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(invite_email.to, [self.users["user"].email])

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")
        uid = invite_link.group("uid")

        self.assertEqual(invite_link.group("scheme"), "http")
        self.assertEqual(invite_link.group("domain"), "front.end.statuscheck")

        response = self.client.get(self.status_url, {"token": token, "uid": "",},)

        self.assertTrue(response.data.get("uid") == ["This field may not be blank."])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_existing_account_check_status_invalid_token(self):
        """
        Request a reset for an existing account and check the status of the resetrequest
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end.statuscheck/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        self.assertEqual(prl.front_end_domain, "front.end.statuscheck")

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(invite_email.to, [self.users["user"].email])

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")
        uid = invite_link.group("uid")

        self.assertEqual(invite_link.group("scheme"), "http")
        self.assertEqual(invite_link.group("domain"), "front.end.statuscheck")

        response = self.client.get(
            self.status_url, {"token": "someinvalidtoken", "uid": uid,},
        )

        self.assertTrue(response.data.get("status") == ["invalid"])
        self.assertTrue(response.data.get("token") == ["Invalid value"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_existing_account_check_status_invalid_uid(self):
        """
        Request a reset for an existing account and check the status of the resetrequest
        """
        response = self.client.post(
            self.url,
            {
                "email": self.users["user"].email,
                "front_end_domain": "http://front.end.statuscheck/",
            },
            format="json",
        )

        self.assertTrue(len(mail.outbox) == 1)
        self.assertTrue(
            response.data.get("detail") == "Password reset request has been processed."
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check whether the request is logged
        prl = PasswordResetLog.objects.get(email=self.users["user"].email)
        self.assertEqual(prl.front_end_domain, "front.end.statuscheck")

        self.assertTrue(len(mail.outbox) == 1)
        invite_email = mail.outbox[0]
        self.assertEqual(invite_email.to, [self.users["user"].email])

        msg = invite_email.body
        invite_link = re.search(
            r"(?P<scheme>http|https):\/\/(?P<domain>[\w\.\-]+)\/account\/reset-password\?token=(?P<token>[\w\-]+)&uid=(?P<uid>[\w\d]+)",
            msg,
            re.I | re.M,
        )

        token = invite_link.group("token")
        uid = invite_link.group("uid")

        self.assertEqual(invite_link.group("scheme"), "http")
        self.assertEqual(invite_link.group("domain"), "front.end.statuscheck")

        response = self.client.get(
            self.status_url, {"token": token, "uid": "someinvaliduid",},
        )

        self.assertTrue(response.data.get("status") == ["invalid"])
        self.assertTrue(response.data.get("uid") == ["Invalid value"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
