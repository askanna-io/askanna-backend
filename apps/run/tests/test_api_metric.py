from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestMetricListAPI(BaseAPITestRun):
    """
    Test to list the RunMetric
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_metrics["run_2"].suuid,
            },
        )

    def test_list_as_askanna_admin(self):
        """
        We can list metrics as an AskAnna admin,
        but response will be empty because of not having access to this workspace.
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_admin(self):
        """
        We can list metrics as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_non_member(self):
        """
        We can list metrics as non_member of a workspace,
        but response will be empty because of not having access to this workspace.
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_anonymous(self):
        """
        Anonymous user can list metrics, but only public ones
        So we expect here an empty list as result
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_member_order_by_metric_name(self):
        """
        We get detail metrics as member of a workspace and order them by metric name
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "order_by": "metric.name",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

        response_reversed = self.client.get(
            self.url,
            {
                "order_by": "-metric.name",
            },
        )
        assert response_reversed.status_code == status.HTTP_200_OK
        assert len(response_reversed.data["results"]) == 4

        assert response.data["results"][0]["metric"]["name"] == response_reversed.data["results"][3]["metric"]["name"]

    def test_list_as_member_filter_metric_name(self):
        """
        We test the filter by metric name
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"metric_name": "Accuracy"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member_filter_label_name(self):
        """
        We test the filter by label name
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"label_name": "product"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4


class TestMetricPublicProjectListAPI(BaseAPITestRun):
    """
    Test to list the Metrics from a job in a public project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_metrics["run_4"].suuid,
            },
        )

    def test_list_as_non_member(self):
        """
        Public project run metrics are listable by members who are not member of the workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_anonymous(self):
        """
        Public project run metrics are listable by anyone who is not authenticated
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2


class TestMetricUpdateAPI(BaseAPITestRun):
    """
    Test updating the metrics of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_metrics.get("run_2").suuid,
                "run__suuid": self.run_metrics.get("run_2").suuid,
            },
        )

    def test_update_as_askanna_admin(self):
        """
        We cannot update metrics as an AskAnna admin who is not member of a workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.put(
            self.url,
            {"metrics": self.metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_admin(self):
        """
        We update metrics as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.put(
            self.url,
            {"metrics": self.metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_update_as_member(self):
        """
        We update metrics as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.put(
            self.url,
            {"metrics": self.metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_update_as_non_member(self):
        """
        We cannot update metrics as non-member of a workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.put(
            self.url,
            {"metrics": self.metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_anonymous(self):
        """
        We cannot update metrics as anonymous
        """
        response = self.client.put(
            self.url,
            {"metrics": self.metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
