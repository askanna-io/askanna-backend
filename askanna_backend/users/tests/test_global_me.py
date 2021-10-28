# -*- coding: utf-8 -*-
from django.urls import reverse
import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

pytestmark = pytest.mark.django_db


class TestMeBase:
    @classmethod
    def setup_class(cls):
        cls.users = {
            "anna": User.objects.create(
                username="anna",
                is_staff=True,
                is_superuser=True,
                email="anna@askanna.dev",
                name="anna",
                job_title="Job Title anna",
            ),
            "admin": User.objects.create(
                username="admin",
                email="admin@askanna.dev",
                name="admin",
                job_title="Job Title admin",
            ),
            "user": User.objects.create(
                username="user",
                email="user@askanna.dev",
                name="user",
                job_title="Job Title user",
            ),
            "user_b": User.objects.create(
                username="user_b",
                email="user_b@askanna.dev",
                name="user_b",
                job_title="Job Title user_b",
            ),
            "user_nonmember": User.objects.create(
                username="user_nonmember",
                email="user_nonmember@askanna.dev",
                name="user_nonmember",
                job_title="Job Title user_nonmember",
            ),
        }

    @classmethod
    def teardown_class(cls):
        """
        Remove all the user instances we had setup for the test
        """
        for _, user in cls.users.items():
            user.delete()


class BaseTestGlobalMeGet(TestMeBase):
    """
    Test to retrieve `/v1/me/`
    """

    def setUp(self):
        self.url = reverse(
            "global-me",
            kwargs={
                "version": "v1",
            },
        )

    def test_me_as_anna(self):
        """
        Anna has all access
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), True)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_admin(self):
        """
        As an admin of a certain workspace, we just get `askanna.member` on global level
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_user(self):
        """
        As an user of a certain workspace, we just get `askanna.member` on global level
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_anonymous(self):
        """
        As anonymous user we can get a /me profile but other than that nothing else
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), False)


class TestGlobalMeGet(BaseTestGlobalMeGet, APITestCase):
    ...


class BaseTestGlobalMePatch(TestMeBase):
    """
    Test to retrieve `/v1/me/`
    """

    def setUp(self):
        self.url = reverse(
            "global-me",
            kwargs={
                "version": "v1",
            },
        )

    def test_me_as_anna(self):
        """
        Anna has all access also in updating own /me
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        update_me_payload = {
            "name": "new name",
            "job_title": "new title",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "new name")
        self.assertEqual(response.data.get("job_title"), "new title")

        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), True)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_admin(self):
        """
        User with name admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        update_me_payload = {
            "name": "new name",
            "job_title": "new title",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "new name")
        self.assertEqual(response.data.get("job_title"), "new title")

        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_user(self):
        """
        Regular user can update /me
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        update_me_payload = {
            "name": "new name",
            "job_title": "new title",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "new name")
        self.assertEqual(response.data.get("job_title"), "new title")

        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_anonymous(self):
        """
        Anonymous cannot update /me
        """
        update_me_payload = {
            "name": "new name",
            "job_title": "new title",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_as_user_partial_name(self):
        """
        Regular user can update /me with only name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        update_me_payload = {
            "name": "new name",
            "job_title": "",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "new name")
        self.assertEqual(response.data.get("job_title"), "")

        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), True)

    def test_me_as_user_partial_jobtitle(self):
        """
        Regular user can update /me with only job_title
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        update_me_payload = {
            "name": "",
            "job_title": "new title",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("name"), "")
        self.assertEqual(response.data.get("job_title"), "new title")

        permissions = response.data.get("permission")
        self.assertTrue(isinstance(permissions, dict))
        self.assertEqual(permissions.get("askanna.me"), True)
        self.assertEqual(permissions.get("askanna.admin"), False)
        self.assertEqual(permissions.get("askanna.member"), True)


class TestGlobalMePatch(BaseTestGlobalMePatch, APITestCase):
    ...


class BaseTestGlobalMeDelete(TestMeBase):
    """
    Test to retrieve `/v1/me/`
    """

    def setUp(self):
        self.url = reverse(
            "global-me",
            kwargs={
                "version": "v1",
            },
        )

    def test_me_as_anna(self):
        """
        Anna has all access also in deleting own /me
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_me_as_admin(self):
        """
        User with name admin can delete itself
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_me_as_user(self):
        """
        Regular user can delete /me
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_me_as_anonymous(self):
        """
        Anonymous cannot delete /me
        """
        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestGlobalMeDelete(BaseTestGlobalMeDelete, APITestCase):
    ...
