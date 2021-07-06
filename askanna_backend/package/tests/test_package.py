# -*- coding: utf-8 -*-
from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from job.tests.base import BaseJobTestDef

pytestmark = pytest.mark.django_db


class TestPackageList(BaseJobTestDef, APITestCase):
    """
    Test on listing packages
    """

    def setUp(self):
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_admin(self):
        """
        We can list package as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_member(self):
        """
        We can list packages as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_as_nonmember(self):
        """
        We cannot list packages as nonmember of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We cannot list packages as member of a workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
