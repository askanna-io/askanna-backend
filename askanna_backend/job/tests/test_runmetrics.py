import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from job.models import JobDef, JobRun, JobPayload
from project.models import Project
from package.models import Package
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership, User
from workspace.models import Workspace

from .base import BaseJobTestDef


class TestMetricsListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the RunMetrics
    """

    def setUp(self):
        self.url = reverse("metric-list", kwargs={"version": "v1"},)

    def test_list_as_admin(self):
        """
        We can list metrics as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_as_nonmember(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We can list metrics as member of a workspace
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMetricsDetailAPI(BaseJobTestDef, APITestCase):
    """
    Test to get detail on specific metrics for a jobrun
    """

    def setUp(self):
        self.url = reverse(
            "metric-detail",
            kwargs={
                "version": "v1",
                "jobrun__short_uuid": self.jobruns.get("run1").short_uuid,
            },
        )

    def test_detail_as_admin(self):
        """
        We can list metrics as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_nonmember(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_anonymous(self):
        """
        We can list metrics as member of a workspace
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

