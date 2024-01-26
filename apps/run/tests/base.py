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
        create_metric_dict_small,
        create_variable_dict_small,
    ):
        self.users = test_users
        self.memberships = test_memberships
        self.packages = test_packages
        self.jobs = test_jobs
        self.runs = test_runs
        self.artifacts = test_run_artifacts
        self.run_logs = test_run_logs

        self.create_metric_dict_small = create_metric_dict_small
        self.create_variable_dict_small = create_variable_dict_small
