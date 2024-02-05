from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestRunLogAPI(BaseAPITestRun):
    """
    Test to get the log of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-log",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_2"].suuid,
            },
        )

    def test_log_as_askanna_admin(self):
        """
        We cannot get the log for a run as an AskAnna admin who is not a member of the workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_admin(self):
        """
        We can get the log for a run as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.run_log

    def test_log_as_member(self):
        """
        We can get the log for a run as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.run_log

    def test_log_as_non_member(self):
        """
        We cannot get the log for a run as a non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_anonymous(self):
        """
        We cannot get the log of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunLogLimitAPI(BaseAPITestRun):
    """
    More tests to get the log of a run and tests the limit parameter
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-log",
            kwargs={"version": "v1", "suuid": self.runs["run_2"].suuid},
        )

    def test_log_as_member(self):
        """
        We can get the log for a run as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.run_log

    def test_log_as_member_partial(self):
        """
        We can get the log for a run as a member with offset and limit
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "offset": 1,
                "limit": 2,
            },
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.run_log[1:3]

    def test_log_as_member_limit_full(self):
        """
        We can get the log for a run as a member with limit set to -1 to get full log
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "offset": 0,
                "limit": -1,
            },
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.run_log

    def test_log_as_member_while_running(self):
        """
        We can get the log for a run as a member while running
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "offset": 5,
                "limit": 5,
            },
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.run_log[-1:]
