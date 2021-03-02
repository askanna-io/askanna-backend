# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import (
    BaseJobTestDef,
    metric_response_good_small,
)


class TestMetricsListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the RunMetrics
    """

    def setUp(self):
        self.url = reverse(
            "run-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run_suuid": self.runmetrics.get("run1").short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list metrics as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

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

    def test_list_as_member_order_by_metricname(self):
        """
        We get detail metrics as member of a workspace, but request the metrics to be returned in reversed sort on name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url + "?ordering=-metric.name", format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        response = self.client.get(self.url + "?ordering=metric.name", format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_metricname(self):
        """
        We test the filter by metric name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        query_params = {"metric_name": "Accuracy"}

        response = self.client.get(self.url, query_params, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class TestMetricsMetaAPI(BaseJobTestDef, APITestCase):
    """
    Test to get meta on specific metrics for a jobrun
    """

    def setUp(self):
        self.url = reverse(
            "run-metric-meta",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.runmetrics.get(
                    "run1"
                ).short_uuid,
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )

    def test_meta_as_member(self):
        """
        Retrieve the meta information about the metrics
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 4)


class TestMetricsUpdateAPI(BaseJobTestDef, APITestCase):
    """
    We update the metrics of a run
    """

    def setUp(self):
        self.url = reverse(
            "run-metric-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.runmetrics.get(
                    "run1"
                ).short_uuid,
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


class JobTestMetricsListAPI(TestMetricsListAPI):
    def setUp(self):
        self.url = reverse(
            "job-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_job_suuid": self.jobdef.short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_member_order_by_metricname(self):
        """
        We get detail metrics as member of a workspace, but request the metrics to be returned in reversed sort on name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url + "?ordering=-metric.name", format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

        response = self.client.get(self.url + "?ordering=metric.name", format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_member_filter_metricname(self):
        """
        We test the filter by metric name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        query_params = {"metric_name": "Accuracy", "job": self.jobdef.short_uuid}

        response = self.client.get(self.url, query_params, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
