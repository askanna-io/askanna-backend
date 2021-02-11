# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import (
    BaseJobTestDef,
    metric_response_good,
    metric_response_good_small,
    metric_response_good_reversed,
)


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
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )

    def test_detail_as_admin(self):
        """
        We get detail metrics as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, metric_response_good)

    def test_detail_as_member(self):
        """
        We get detail metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, metric_response_good)

    def test_detail_as_nonmember(self):
        """
        As a non-member we cannot get the details for a jobrun and it's metrics
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_as_anonymous(self):
        """
        We get not get detail metrics as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_as_member_reversed(self):
        """
        We get detail metrics as member of a workspace, but request the metrics to be returned in reversed sort on name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url + "?ordering=-metric.name", format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, metric_response_good_reversed)

    def test_detail_as_member_reversed_with_limit_2(self):
        """
        We get detail metrics as member of a workspace, but request the metrics to be returned in reversed sort on name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url + "?ordering=-metric.name&limit=2&offset=0",
            format="json",
            HTTP_HOST="testserver",
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get("results"), metric_response_good_reversed[0:2]
        )
        self.assertEqual(response.data.get("count"), 4)

    def test_detail_as_member_metricsmeta(self):
        """
        Retrieve the meta information about the metrics
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url + "meta/", format="json", HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 4)


class TestMetricsUpdateAPI(BaseJobTestDef, APITestCase):
    """
    We update the metrics of a run
    """

    def setUp(self):
        self.url = reverse(
            "metric-detail",
            kwargs={
                "version": "v1",
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )

    def test_update_as_admin(self):
        """
        We update metrics as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(
            self.url, {"metrics": metric_response_good_small}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        print(metric_response_good_small)
        self.assertEqual(response.data, metric_response_good_small)

    def test_update_as_member(self):
        """
        We update metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(
            self.url, {"metrics": metric_response_good_small}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, metric_response_good_small)

    def test_update_as_nonmember(self):
        """
        We cannot update metrics as nonmember of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(
            self.url, {"metrics": metric_response_good_small}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_anonymous(self):
        """
        We cannot update metrics as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProjectTestMetricsListAPI(TestMetricsListAPI):
    def setUp(self):
        self.url = reverse(
            "project-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__jobdef__project__short_uuid": self.project.short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list metrics as admin of a workspace, by project
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
        self.assertEqual(len(response.data), 2)


class JobTestMetricsListAPI(TestMetricsListAPI):
    def setUp(self):
        self.url = reverse(
            "job-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class ProjectTestMetricsDetailAPI(TestMetricsDetailAPI):
    def setUp(self):
        self.url = reverse(
            "project-metric-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__jobdef__project__short_uuid": self.project.short_uuid,
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )


class JobTestMetricsDetailAPI(TestMetricsDetailAPI):
    def setUp(self):
        self.url = reverse(
            "job-metric-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__jobdef__short_uuid": self.jobdef.short_uuid,
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )
