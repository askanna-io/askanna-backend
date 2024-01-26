from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestRunMetricsListAPI(BaseAPITestRun):
    """
    Test to get the list of Run Metrics for a specifc run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_2"].suuid,
            },
        )

    def test_get_run_metric_list(self) -> bool:
        def _test_get_run_metric_list(user_name: str | None = None, expect_no_access: bool = False) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.get(self.url)
            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND if user_name else status.HTTP_401_UNAUTHORIZED
                return True

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data["results"]) == 4

            return True

        assert _test_get_run_metric_list(user_name="workspace_admin") is True
        assert _test_get_run_metric_list(user_name="workspace_member") is True
        assert _test_get_run_metric_list(user_name="workspace_viewer") is True

        assert _test_get_run_metric_list(user_name="askanna_super_admin", expect_no_access=True) is True
        assert _test_get_run_metric_list(user_name="no_workspace_member", expect_no_access=True) is True
        assert _test_get_run_metric_list(expect_no_access=True) is True  # anonymous

    def test_get_public_run_metric_list(self) -> bool:
        def _test_get_run_metric_list(user_name: str | None = None) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.get(
                reverse(
                    "run-variable-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": self.runs["run_4"].suuid,
                    },
                )
            )

            assert response.status_code == status.HTTP_200_OK
            assert len(response.data["results"]) == 2

            return True

        assert _test_get_run_metric_list(user_name="askanna_super_admin") is True
        assert _test_get_run_metric_list(user_name="workspace_admin") is True
        assert _test_get_run_metric_list(user_name="workspace_member") is True
        assert _test_get_run_metric_list(user_name="workspace_viewer") is True
        assert _test_get_run_metric_list(user_name="no_workspace_member") is True
        assert _test_get_run_metric_list() is True  # anonymous

    def test_list_as_member_order_by_metric_name(self):
        """
        We get detail run metrics as member of a workspace and order them by metric name
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
            {"label_name": "Missing data"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2


class TestRunMetricsUpdateAPI(BaseAPITestRun):
    """
    Tests related to updating the run metrics for a specific run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_2"].suuid,
            },
        )

    def test_update_run_metric(self):
        def _test_update_run_metric(user_name: str | None = None, expect_no_access: bool = False) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.patch(
                self.url,
                {"metrics": self.create_metric_dict_small(self.runs["run_2"].suuid)},
                format="json",
            )

            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND if user_name else status.HTTP_401_UNAUTHORIZED
                return True

            assert response.status_code == status.HTTP_204_NO_CONTENT

            return True

        assert _test_update_run_metric(user_name="workspace_admin") is True
        assert _test_update_run_metric(user_name="workspace_member") is True

        assert _test_update_run_metric(user_name="askanna_super_admin", expect_no_access=True) is True
        assert _test_update_run_metric(user_name="workspace_viewer", expect_no_access=True) is True
        assert _test_update_run_metric(user_name="no_workspace_member", expect_no_access=True) is True
        assert _test_update_run_metric(expect_no_access=True) is True  # anonymous

    def test_update_run_metric_locked_run(self):
        # Set the lock
        lock_key = f"run.RunMetric:update:{self.runs['run_2'].suuid}"
        cache.set(lock_key, True, timeout=60)

        # Try to update the RunVariable
        self.set_authorization(self.users["workspace_member"])
        response = response = self.client.patch(
            self.url,
            {"metrics": self.create_metric_dict_small(self.runs["run_2"].suuid)},
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data == {"detail": "These run's metrics are currently being updated"}

        cache.delete(lock_key)
