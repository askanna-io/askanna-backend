import pytest

from tests import AskAnnaAPITestCase


class BaseAPITestRun(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(
        self,
        test_users,
        test_memberships,
        test_packages,
        test_jobs,
        test_runs,
        test_run_artifacts,
        test_run_logs,
        test_run_metrics,
        test_run_variables,
        metric_response_good_small,
        variable_response_good_small,
    ):
        self.users = test_users
        self.memberships = test_memberships
        self.packages = test_packages
        self.jobs = test_jobs
        self.runs = test_runs
        self.artifacts = test_run_artifacts
        self.run_logs = test_run_logs
        self.run_metrics = test_run_metrics
        self.run_variables = test_run_variables

        self.metric_response_good_small = metric_response_good_small
        self.variable_response_good_small = variable_response_good_small
