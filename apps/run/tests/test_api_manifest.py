from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestRunManifestAPI(BaseAPITestRun):
    """
    Test to get manifest of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-manifest",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_1"].suuid,
            },
        )

    def test_manifest_as_askanna_admin(self):
        """
        We cannot get the manifest for a run as an AskAnna admin who is not a member of the workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_manifest_as_admin(self):
        """
        We can get the manifest for a run as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "python my_script.py" in str(response.content)

    def test_manifest_as_member(self):
        """
        We can get the manifest for a run as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "python my_script.py" in str(response.content)

    def test_manifest_as_viewer(self):
        """
        We cannot get the manifest for a run as a viewer
        """
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_manifest_as_non_member(self):
        """
        We cannot get the manifest for a run as a non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

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
        self.set_authorization(self.users["workspace_member"])

        url = reverse(
            "run-manifest",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_5"].suuid,
            },
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "AskAnna could not find the file:" in str(response.content)

    def test_manifest_as_member_job_not_found(self):
        """
        The job is not found in askanna.yml
        """
        self.set_authorization(self.users["workspace_member"])

        url = reverse(
            "run-manifest",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_3"].suuid,
            },
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "AskAnna could not start the job" in str(response.content)
