from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseRunTest


class TestRunLogAPI(BaseRunTest, APITestCase):
    """
    Test to get the log of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-log",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run1"].suuid,
            },
        )

    def test_log_as_askanna_admin(self):
        """
        We cannot get the log for a run as an AskAnna admin who is not a member of the workspace
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_admin(self):
        """
        We can get the log for a run as an admin
        """
        self.activate_user("admin")

        response = self.client.get(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.runlog["run1"].stdout  # type: ignore

    def test_log_as_member(self):
        """
        We can get the log for a run as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.runlog["run1"].stdout  # type: ignore

    def test_log_as_non_member(self):
        """
        We cannot get the log for a run as a non-member
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_anonymous(self):
        """
        We cannot get the log of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunLogLimitAPI(BaseRunTest, APITestCase):
    """
    More tests to get the log of a run and tests the limit parameter
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-log",
            kwargs={"version": "v1", "suuid": self.runs["run1"].suuid},
        )
        self.url2 = reverse(
            "run-log",
            kwargs={"version": "v1", "suuid": self.runs["run2"].suuid},
        )
        self.url3 = reverse(
            "run-log",
            kwargs={"version": "v1", "suuid": self.runs["run5"].suuid},
        )

    def test_log_as_askanna_admin(self):
        """
        We cannot get the log for a run as an AskAnna admin who is not a member of the workspace
        """
        self.activate_user("anna")
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_admin(self):
        """
        We can get the log for a run as an admin
        """
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.runlog["run1"].stdout  # type: ignore

    def test_log_as_member(self):
        """
        We can get the log for a run as a member
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.runlog["run1"].stdout  # type: ignore

    def test_log_as_non_member(self):
        """
        We cannot get the log for a run as a non-member
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_anonymous(self):
        """
        We can NOT get the log of a run as anonymous user
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_log_as_member_partial(self):
        """
        We can get the log for a run as a member with offset and limit
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "offset": 1,
                "limit": 2,
            },
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.runlog["run1"].stdout[1:3]  # type: ignore

    def test_log_as_member_limit_full(self):
        """
        We can get the log for a run as a member with limit set to -1 to get full log
        """
        self.activate_user("member")
        response = self.client.get(
            self.url2,
            {
                "offset": 0,
                "limit": -1,
            },
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == self.runlog["run2"].stdout  # type: ignore

    def test_log_as_member_while_running(self):
        """
        We can get the log for a run as a member while running
        """
        self.activate_user("member")
        response = self.client.get(
            self.url3,
            {
                "offset": 5,
                "limit": 5,
            },
            HTTP_HOST="testserver",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore
