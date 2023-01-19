from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseRunTest


class TestRunManifestAPI(BaseRunTest, APITestCase):
    """
    Test to get manifest of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-manifest",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run1"].suuid,
            },
        )

    def test_manifest_as_askanna_admin(self):
        """
        We cannot get the manifest for a run as an AskAnna admin who is not a member of the workspace
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_manifest_as_admin(self):
        """
        We can get the manifest for a run as an admin
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0  # type: ignore

    def test_manifest_as_member(self):
        """
        We can get the manifest for a run as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0  # type: ignore

    def test_manifest_as_non_member(self):
        """
        We cannot get the manifest for a run as a non-member
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_manifest_as_anonymous(self):
        """
        We cannot get the manifest of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_manifest_as_member_no_config_found(self):
        """
        There is no askanna.yml found
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "AskAnna could not find the file:" in str(response.content)

    def test_manifest_as_member_job_not_found(self):
        """
        The job is not found in askanna.yml
        """
        self.activate_user("member2")
        url = reverse(
            "run-manifest",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run3"].suuid,
            },
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "AskAnna could not start the job" in str(response.content)

    def test_manifest_as_member_correct_job(self):
        """
        The job is found in askanna.yml
        """
        self.activate_user("member2")

        url = reverse(
            "run-manifest",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run4"].suuid,
            },
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "python my_script.py" in str(response.content)
