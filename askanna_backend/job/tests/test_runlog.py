# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef


class TestJobRunLogAPI(BaseJobTestDef, APITestCase):

    """
    Test to get log of a Jobrun
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "runinfo-log",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )

    def test_log_as_admin(self):
        """
        We can get the log for a jobrun as an admin
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_member(self):
        """
        We can get the log for a jobrun as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_nonmember(self):
        """
        We can NOT get the log for a jobrun as a non-member
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_as_anonymous(self):
        """
        We can NOT get the log of a jborun as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestJobRunLogShortCutAPI(TestJobRunLogAPI):
    """
    Test to get log of a Jobrun
    Shortcut version
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "shortcut-jobrun-log",
            kwargs={"short_uuid": self.jobruns["run1"].short_uuid},
        )
