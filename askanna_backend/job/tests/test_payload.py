from django.urls import reverse
from job.models import JobPayload
from rest_framework import status
from rest_framework.test import APITestCase
from run.models import Run

from .base import BaseJobTestDef


class BasePayload(BaseJobTestDef, APITestCase):
    def setUp(self):
        super().setUp()
        self.startjob_url = reverse(
            "job-new-run",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )

        self.setUpPayload()

        self.url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["after_payload"].suuid,
            },
        )

    def setUpPayload(self):
        """
        Prep a payload for every test
        """
        self.activate_user("admin")

        response = self.client.post(
            self.startjob_url,
            {
                "example_payload": "startjob",
                "multirow": True,
                "someothervar": "yes",
            },
            format="json",
            HTTP_HOST="testserver",
        )
        self.runs["after_payload"] = Run.objects.get(suuid=response.data["suuid"])  # type: ignore
        assert response.status_code == status.HTTP_201_CREATED
        self.client.credentials()  # type: ignore


class TestRunPayloadAPI(BasePayload):
    """
    Test get back the list of payloads of a run
    """

    def test_list_as_askanna_admin(self):
        """
        We cannot get the payload as an AskAnna admin because it's a run in a private project
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_admin(self):
        """
        We can get the payload as an admin
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_member(self):
        """
        We can get the payload as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_non_member(self):
        """
        We cannot get the payload as a non-member because it's a run in a private project
        """
        self.activate_user("non_member")
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_anonymous(self):
        """
        We cannot get the payload as anonymous because it's a run in a private project
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore


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
                "parent_lookup_run__suuid": self.runs["after_payload"].suuid,
                "suuid": self.payload.suuid,
            },
        )

    def setUpPayload(self):
        super().setUpPayload()
        self.activate_user("admin")

        run_payload_list_url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["after_payload"].suuid,
            },
        )
        response = self.client.get(run_payload_list_url)
        assert response.status_code == status.HTTP_200_OK

        self.payload = JobPayload.objects.get(suuid=response.data["results"][0]["suuid"])  # type: ignore

        self.client.credentials()  # type: ignore

    def check_content(self, response):
        assert response.data["example_payload"] == "startjob"
        assert response.data["multirow"] is True
        assert response.data["someothervar"] == "yes"

        return True

    def test_list_as_askanna_admin(self):
        """
        We cannot get the payload as an AskAnna admin because it's a run in a private project
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_as_admin(self):
        """
        We can get the payload as an admin
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert self.check_content(response) is True

    def test_list_as_member(self):
        """
        We can get the payload as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert self.check_content(response) is True

    def test_list_as_non_member(self):
        """
        We cannot get the payload as a non-member because it's a run in a private project
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_as_anonymous(self):
        """
        We cannot get the payload as anonymous because it's a run in a private project
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
