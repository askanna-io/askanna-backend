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
            kwargs={"version": "v1", "suuid": self.runs["run1"].suuid},
        )

    def test_log_as_admin(self):
        """
        We can get the log for a run as an admin
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_member(self):
        """
        We can get the log for a run as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_nonmember(self):
        """
        We can NOT get the log for a run as a non-member
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_as_anonymous(self):
        """
        We can NOT get the log of a run as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestMoreRunLogAPI(BaseRunTest, APITestCase):

    """
    More tests to get the log of a Run
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

    def test_log_as_admin(self):
        """
        We can get the log for a run as an admin
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_member(self):
        """
        We can get the log for a run as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_nonmember(self):
        """
        We can NOT get the log for a run as a non-member
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_as_anonymous(self):
        """
        We can NOT get the log of a run as anonymous user
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_as_member_partial(self):
        """
        We can get the log for a run as a member but partial log
        """
        self.activate_user("member")

        query_params = {"offset": 1, "limit": 2}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(len(response.data.get("results")), 2)

    def test_log_as_member_partial_full(self):
        """
        We can get the log for a run as a member but partial full
        """
        self.activate_user("member")

        query_params = {"offset": 0, "limit": 1000}

        response = self.client.get(
            self.url2,
            query_params,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(len(response.data.get("results")), 6)

    def test_log_as_member_while_running(self):
        """
        We can get the log for a run as a member while running
        """
        self.activate_user("member")

        query_params = {"offset": 5, "limit": 5}

        response = self.client.get(
            self.url3,
            query_params,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(len(response.data.get("results")), 4)
