import json

from django.urls import reverse
from rest_framework import status

from job.tests.base import BaseAPITestJob


class TestJobRunRequestAPI(BaseAPITestJob):
    """
    Test starting a run for a job
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-new-run",
            kwargs={
                "version": "v1",
                "suuid": self.jobs["my-test-job"].suuid,
            },
        )

    def test_start_job_as_askanna_admin(self):
        """
        We cannot start a job as an AskAnna admin
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.post(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_job_as_admin(self):
        """
        We can start a job as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.post(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

    def test_start_job_as_member(self):
        """
        We can start a job as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.post(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

    def test_start_job_as_non_member(self):
        """
        We cannot start a job as a non-member of the jobdef
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.post(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_startjob_as_anonymous(self):
        """
        We cannot start jobs as anonymous
        """
        response = self.client.post(self.url, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_startjob_with_invalid_json(self):
        """
        Starting jobs with invalid json is not possible
        in this case the json is posted as string
        """
        self.set_authorization(self.users["workspace_member"])

        payload = json.dumps({"example_payload": "startjob"})
        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "The JSON data payload is not valid, please check and try again" in str(response.content)

    def test_startjob_with_payload_in_uri(self):
        """
        We can start jobs with payload given in the uri (as get arguments)
        """
        self.set_authorization(self.users["workspace_member"])

        payload = {"example_payload": "startjob"}
        response = self.client.post(self.url, payload, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

    def test_startjob_with_payload_empty(self):
        """
        We can start jobs with empty payload
        """
        self.set_authorization(self.users["workspace_member"])

        payload = None
        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

    def test_startjob_with_payload_in_uri_empty(self):
        """
        We can start jobs with empty payload given by the uri
        """
        self.set_authorization(self.users["workspace_member"])

        payload = None
        response = self.client.post(self.url, payload, HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

    def test_startjob_with_askanna_agents(self):
        """
        We can start a job as different askanna-agents
        """
        self.set_authorization(self.users["workspace_member"])

        for agent, trigger in {
            "webui": "webui",
            "cli": "cli",
            "python-sdk": "python-sdk",
            "worker": "worker",
            "invalid": "api",
            "029340892098340280": "api",
        }.items():
            response = self.client.post(
                self.url,
                format="json",
                HTTP_HOST="testserver",
                HTTP_ASKANNA_AGENT=agent,
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["status"] == "queued"

            runinfo = self.client.get(
                reverse(
                    "run-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": response.data.get("suuid"),
                    },
                )
            )
            assert runinfo.status_code == status.HTTP_200_OK
            assert runinfo.data.get("status") == "queued"
            assert runinfo.data.get("trigger") == trigger.upper()
