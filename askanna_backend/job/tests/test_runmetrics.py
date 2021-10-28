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
        super().setUp()
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
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_nonmember(self):
        """
        Non members cannot list metrics from a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_anonymous(self):
        """
        Anonymous user can list metrics, but only public ones
        So we expect here an empty list as result
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_member_order_by_metricname(self):
        """
        We get detail metrics as member of a workspace, but request the metrics to be returned in reversed sort on name
        """
        self.activate_user("member")

        response = self.client.get(
            self.url + "?ordering=-metric.name",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        response = self.client.get(
            self.url + "?ordering=metric.name",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_metricname(self):
        """
        We test the filter by metric name
        """
        self.activate_user("member")

        query_params = {"metric_name": "Accuracy"}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_member_filter_labelname(self):
        """
        We test the filter by label name
        """
        self.activate_user("member")

        query_params = {"label_name": "product"}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)


class TestMetricsMetaAPI(BaseJobTestDef, APITestCase):
    """
    Test to get meta on specific metrics for a jobrun
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-meta",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )

    def test_meta_as_admin(self):
        """
        Retrieve the meta information about the metrics
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 4)

    def test_meta_as_member(self):
        """
        Retrieve the meta information about the metrics
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 4)

    def test_meta_as_nonmember(self):
        """
        Retrieve the meta information about the metrics
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_meta_as_anonymous(self):
        """
        Retrieve the meta information about the metrics
        """
        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestMetricsPublicProjectMetaAPI(TestMetricsMetaAPI):
    """
    Test to get meta on specific metrics for a jobrun within a public project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-meta",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
                "jobrun__short_uuid": self.runmetrics.get("run6").short_uuid,
            },
        )

    def test_meta_as_nonmember(self):
        """
        Retrieve the meta information about the metrics
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_meta_as_anonymous(self):
        """
        Retrieve the meta information about the metrics
        """
        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestMetricsUpdateAPI(BaseJobTestDef, APITestCase):
    """
    We update the metrics of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
                "jobrun__short_uuid": self.runmetrics.get("run1").short_uuid,
            },
        )

    def test_update_as_admin(self):
        """
        We update metrics as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, metric_response_good_small)

    def test_update_as_member(self):
        """
        We update metrics as member of a workspace
        """
        self.activate_user("member")

        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, metric_response_good_small)

    def test_update_as_nonmember(self):
        """
        We cannot update metrics as nonmember of a workspace
        """
        self.activate_user("non_member")

        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_anonymous(self):
        """
        We cannot update metrics as anonymous
        """
        response = self.client.put(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JobTestMetricsListAPI(TestMetricsListAPI):
    def setUp(self):
        super().setUp()
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
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_nonmember(self):
        """
        Non members cannot list metrics from a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_anonymous(self):
        """
        Anonymous user can only list metrics from a public project
        Here we expect an empty list as this run was in a private project
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_member_order_by_metricname(self):
        """
        We get detail metrics as member of a workspace,
          but request the metrics to be returned in reversed sort on name
        """
        self.activate_user("member")

        response = self.client.get(
            self.url + "?ordering=-metric.name",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

        response = self.client.get(
            self.url + "?ordering=metric.name",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_member_filter_metricname(self):
        """
        We test the filter by metric name
        """
        self.activate_user("member")

        query_params = {"metric_name": "Accuracy", "job": self.jobdef.short_uuid}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_labelname(self):
        """
        We test the filter by label name
        """
        self.activate_user("member")

        query_params = {"label_name": "product"}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
