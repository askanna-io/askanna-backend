# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef, metric_response_good, metric_response_good_small


class TestRunMetricsModel(BaseJobTestDef, APITestCase):
    """
    Test RunMetrics model functions
    """

    def test_runmetrics_function_load_from_file(self):
        self.assertEqual(self.runmetrics["run1"].load_from_file(), metric_response_good)

    def test_runmetrics_function_update_meta_no_metrics_and_no_labels(self):
        modified_before = self.runmetrics["run7"].modified
        self.runmetrics["run7"].update_meta()
        self.assertEqual(self.runmetrics["run7"].modified, modified_before)

        self.assertEqual(self.runmetrics["run7"].count, 0)
        self.assertEqual(self.runmetrics["run7"].size, 0)
        self.assertIsNone(self.runmetrics["run7"].metric_names)
        self.assertIsNone(self.runmetrics["run7"].label_names)

    def test_runmetrics_function_update_meta(self):
        modified_before_1 = self.runmetrics["run7"].modified
        self.runmetrics["run7"].update_meta()
        self.assertEqual(self.runmetrics["run7"].modified, modified_before_1)

        self.assertEqual(self.runmetrics["run7"].count, 0)
        self.assertEqual(self.runmetrics["run7"].size, 0)
        self.assertIsNone(self.runmetrics["run7"].metric_names)
        self.assertIsNone(self.runmetrics["run7"].label_names)

        self.runmetrics["run7"].metrics = metric_response_good
        self.runmetrics["run7"].save()

        modified_before_2 = self.runmetrics["run7"].modified
        self.runmetrics["run7"].update_meta()
        self.assertEqual(self.runmetrics["run7"].modified, modified_before_2)

        self.assertEqual(self.runmetrics["run7"].count, 4)
        self.assertEqual(self.runmetrics["run7"].size, 1190)
        self.assertEqual(
            self.runmetrics["run7"].metric_names,
            [{"name": "Accuracy", "type": "integer", "count": 2}, {"name": "Quality", "type": "string", "count": 2}],
        )
        self.assertEqual(
            self.runmetrics["run7"].label_names,
            [
                {"name": "city", "type": "string"},
                {"name": "product", "type": "string"},
                {"name": "Missing data", "type": "boolean"},
            ],
        )

    def test_runmetrics_function_update_meta_no_labels(self):
        self.runmetrics["run6"].update_meta()
        self.assertEqual(self.runmetrics["run6"].count, 2)
        self.assertEqual(self.runmetrics["run6"].size, 334)
        self.assertIsNotNone(self.runmetrics["run6"].metric_names)
        self.assertIsNone(self.runmetrics["run6"].label_names)


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
