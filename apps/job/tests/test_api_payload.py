from django.urls import reverse
from rest_framework import status

from job.models import JobPayload
from job.tests.base import BaseAPITestJob
from run.models import Run


class BasePayload(BaseAPITestJob):
    def setUp(self):
        super().setUp()
        self.startjob_url = reverse(
            "job-new-run",
            kwargs={
                "version": "v1",
                "suuid": self.jobs["my-test-job"].suuid,
            },
        )

        self.set_payload()

        self.url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_after_payload.suuid,
            },
        )

    def set_payload(self):
        """
        Prep a payload for every test
        """
        self.set_authorization(self.users["workspace_admin"])

        payload = {
            "example_payload": "startjob",
            "multirow": True,
            "someothervar": "yes",
        }

        response = self.client.post(self.startjob_url, payload, format="json", HTTP_HOST="testserver")
        self.run_after_payload = Run.objects.get(suuid=response.data["suuid"])
        assert response.status_code == status.HTTP_201_CREATED
        self.client.credentials()

    def tearDown(self):
        super().tearDown()
        self.run_after_payload.delete()


class TestRunPayloadAPI(BasePayload):
    """
    Test get back the list of payloads of a run
    """

    def test_list_as_askanna_admin(self):
        """
        We cannot get the payload as an AskAnna admin because it's a run in a private project
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_admin(self):
        """
        We can get the payload as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member(self):
        """
        We can get the payload as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_non_member(self):
        """
        We cannot get the payload as a non-member because it's a run in a private project
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_anonymous(self):
        """
        We cannot get the payload as anonymous because it's a run in a private project
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


class TestRunPayloadRetrieveAPI(BasePayload):
    """
    Test get the payload (content) of a run
    """

    def setUp(self):
        super().setUp()

        self.url = reverse(
            "run-payload-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_after_payload.suuid,
                "suuid": self.payload.suuid,
            },
        )

    def set_payload(self):
        super().set_payload()
        self.set_authorization(self.users["workspace_admin"])

        run_payload_list_url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_after_payload.suuid,
            },
        )
        response = self.client.get(run_payload_list_url)
        assert response.status_code == status.HTTP_200_OK

        self.payload = JobPayload.objects.get(suuid=response.data["results"][0]["suuid"])

        self.client.credentials()

    def tearDown(self):
        super().tearDown()
        self.payload.delete()

    def check_content(self, response):
        assert response.data["example_payload"] == "startjob"
        assert response.data["multirow"] is True
        assert response.data["someothervar"] == "yes"

        return True

    def test_list_as_askanna_admin(self):
        """
        We cannot get the payload as an AskAnna admin because it's a run in a private project
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_as_admin(self):
        """
        We can get the payload as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert self.check_content(response) is True

    def test_list_as_member(self):
        """
        We can get the payload as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert self.check_content(response) is True

    def test_list_as_non_member(self):
        """
        We cannot get the payload as a non-member because it's a run in a private project
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_as_anonymous(self):
        """
        We cannot get the payload as anonymous because it's a run in a private project
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
