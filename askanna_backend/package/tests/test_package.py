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
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_anna(self):
        """
        Package listing is not possible for anna as anna is not part of any workspace/project
        """
        self.activate_user("anna")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_admin(self):
        """
        We can list package as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member(self):
        """
        We can list packages as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_nonmember(self):
        """
        As non member we can only list "public" packages
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_anonymous(self):
        """
        Anonymous can only list packages from public projects
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ProjectTestPackageList(TestPackageList):
    """
    Test on listing packages
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-package-list",
            kwargs={
                "version": "v1",
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list package as admin of a workspace
        """
        self.activate_user("admin")

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
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_nonmember(self):
        """
        We cannot list packages as nonmember of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        Anonymous cannot list packages from private project
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ProjectPublicTestPackageList(TestPackageList):
    """
    Test on listing packages
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-package-list",
            kwargs={
                "version": "v1",
                "parent_lookup_project__short_uuid": self.project3.short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list package as admin of a public workspace
        """
        self.activate_user("admin")

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
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_nonmember(self):
        """
        We cannot list packages as nonmember of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_anonymous(self):
        """
        We cannot list packages as member of a workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
