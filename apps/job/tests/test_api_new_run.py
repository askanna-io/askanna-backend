import json

from django.urls import reverse
from rest_framework import status

from job.tests.base import BaseAPITestJob
from run.models import Run


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

    def _test_new_run(self, user_name: str = None, expect_no_permission: bool = False):
        self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.post(self.url)

        assert (
            response.status_code == status.HTTP_201_CREATED
            if expect_no_permission is False
            else status.HTTP_404_NOT_FOUND
        )

        if expect_no_permission is True:
            assert len(callbacks) == 0
        else:
            assert response.data["status"] == "queued"
            assert len(callbacks) == 1

        return True

    def test_start_new_run_as_askanna_admin(self):
        """
        We cannot start a job as an AskAnna admin
        """
        assert self._test_new_run(user_name="askanna_super_admin", expect_no_permission=True) is True

    def test_start_new_run_as_admin(self):
        """
        We can start a job as an admin
        """
        assert self._test_new_run(user_name="workspace_admin") is True

    def test_start_new_run_as_member(self):
        """
        We can start a job as a member
        """
        assert self._test_new_run(user_name="workspace_member") is True

    def test_start_new_run_as_viewer(self):
        """
        We cannot start a job as a non-member of the jobdef
        """
        assert self._test_new_run(user_name="workspace_viewer", expect_no_permission=True) is True

    def test_start_new_run_as_non_member(self):
        """
        We cannot start a job as a non-member of the jobdef
        """
        assert self._test_new_run(user_name="no_workspace_member", expect_no_permission=True) is True

    def test_start_new_run_as_anonymous(self):
        """
        We cannot start jobs as anonymous
        """
        assert self._test_new_run(expect_no_permission=True) is True

    def test_start_new_run_with_payload(self):
        """
        We can start jobs with JSON payload
        """
        self.set_authorization(self.users["workspace_member"])

        payload = {"example_payload": "startjob"}
        response = self.client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

        run_suuid = response.data["suuid"]
        run = Run.objects.get(suuid=run_suuid)

        assert run.payload_file is not None
        assert run.payload_file.name == "payload.json"
        assert run.payload_file.size == len(json.dumps(payload))
        assert run.payload_file.etag is not None
        assert run.payload_file.content_type == "application/json"
        assert run.payload_file.file.read() == json.dumps(payload).encode()

    def test_start_new_run_with_invalid_json(self):
        """
        Starting jobs with invalid json is not possible
        """
        self.set_authorization(self.users["workspace_member"])

        payload = "test"
        response = self.client.post(self.url, data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "The JSON data payload is not valid, please check the payload and try again" in str(response.content)

    def test_start_new_run_with_empty_payload(self):
        """
        We can start jobs with empty payload
        """
        self.set_authorization(self.users["workspace_member"])

        payload = None
        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "queued"

        run_suuid = response.data["suuid"]
        run = Run.objects.get(suuid=run_suuid)

        assert run.payload_file is None

    def test_start_new_run_with_askanna_agents(self):
        """
        We can start a job as different askanna-agents
        """
        self.set_authorization(self.users["workspace_member"])

        for agent, trigger in {
            "webui": "WEBUI",
            "cli": "CLI",
            "python-sdk": "PYTHON-SDK",
            "worker": "WORKER",
            "invalid": "API",
            "029340892098340280": "API",
        }.items():
            response = self.client.post(self.url, HTTP_ASKANNA_AGENT=agent)

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["status"] == "queued"

            run_suuid = response.data["suuid"]
            run = Run.objects.get(suuid=run_suuid)

            assert run.trigger == trigger
