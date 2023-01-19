from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseRunTest


class TestRunStatusAPI(BaseRunTest, APITestCase):
    """
    Test to get result of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-status",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run1"].suuid,
            },
        )

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot get the status for a run as an AskAnna admin who is not a member of the workspace
        """
        self.activate_user("anna")
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_admin(self):
        """
        We can get the status for a run as an admin
        """
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "finished"  # type: ignore
        assert response.data["duration"] == 50646  # type: ignore

    def test_retrieve_as_member(self):
        """
        We can get the status for a run as a member
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "finished"  # type: ignore
        assert response.data["duration"] == 50646  # type: ignore

    def test_retrieve_as_non_member(self):
        """
        We cannot get the status for a run as a non-member
        """
        self.activate_user("non_member")
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
