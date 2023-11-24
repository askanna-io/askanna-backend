import pytest

from tests import AskAnnaAPITestCase


class BaseAPITestJob(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_memberships, test_projects, test_jobs):
        self.users = test_users
        self.projects = test_projects
        self.jobs = test_jobs
