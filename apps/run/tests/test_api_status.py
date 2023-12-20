from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestRunStatusAPI(BaseAPITestRun):
    """
    Test to get result of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-status",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_2"].suuid,
            },
        )

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot get the status for a run as an AskAnna admin who is not a member of the workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_admin(self):
        """
        We can get the status for a run as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "finished"
        assert response.data["duration"] > 0

    def test_retrieve_as_member(self):
        """
        We can get the status for a run as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "finished"
        assert response.data["duration"] > 0

    def test_retrieve_as_viewer(self):
        """
        We can get the status for a run as a member
        """
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "finished"
        assert response.data["duration"] > 0

    def test_retrieve_as_non_member(self):
        """
        We cannot get the status for a run as a non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the status of a run as anonymous
        """
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
