from django.urls import reverse
from job.models import JobPayload
from rest_framework import status
from rest_framework.test import APITestCase
from run.models import Run

from .base import BaseJobTestDef


class TestJobPayloadAPI(BaseJobTestDef, APITestCase):
    """
    Test Getting back the payload of a job
    """

    def setUp(self):
        super().setUp()
        self.startjob_url = reverse(
            "run-job",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )
        self.url = reverse(
            "job-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobdef__suuid": self.jobdef.suuid,
            },
        )
        self.setUpPayload()

    def setUpPayload(self):
        """
        Prep a payload for every test
        """
        self.activate_user("admin")

        payload = {
            "example_payload": "startjob",
            "multirow": True,
            "someothervar": "yes",
        }

        response = self.client.post(self.startjob_url, payload, format="json", HTTP_HOST="testserver")
        self.runs["after_payload"] = Run.objects.get(suuid=response.data.get("suuid"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    def test_list_as_admin(self):
        """
        We can get the payload as an admin
        """
        self.activate_user("admin")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_member(self):
        """
        We can get the payload as a member
        """
        self.activate_user("member")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_nonmember(self):
        """
        We can NOT get the payload as a non-member
        """
        self.activate_user("non_member")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We can only get payloads from public projects/jobs
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class TestRunPayloadAPI(TestJobPayloadAPI):

    """
    Test getting back the payload of a run
    """

    def setUp(self):
        super().setUp()
        self.startjob_url = reverse(
            "run-job",
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


class TestJobPayloadRetrieveAPI(BaseJobTestDef, APITestCase):
    """
    Test Getting back the payload of a job
    """

    def setUp(self):
        super().setUp()
        self.startjob_url = reverse(
            "run-job",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )
        self.setUpPayload()
        self.url = reverse(
            "job-payload-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobdef__suuid": self.jobdef.suuid,
                "suuid": self.payload.suuid,
            },
        )

    def setUpPayload(self):
        """
        Prep a payload for every test
        """
        self.activate_user("admin")

        payload = {
            "example_payload": "startjob",
            "multirow": True,
            "someothervar": "yes",
        }

        response = self.client.post(self.startjob_url, payload, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.runs["after_payload"] = Run.objects.get(suuid=response.data.get("suuid"))
        # get the payload of this run

        run_payload_list_url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["after_payload"].suuid,
            },
        )
        response = self.client.get(run_payload_list_url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payload = JobPayload.objects.get(suuid=response.data[0]["suuid"])

        self.client.credentials()

    def check_content(self, response):
        self.assertEqual(response.data.get("example_payload"), "startjob")
        self.assertEqual(response.data.get("multirow"), True)
        self.assertEqual(response.data.get("someothervar"), "yes")

    def test_list_as_admin(self):
        """
        We can get the payload as an admin
        """
        self.activate_user("admin")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_content(response)

    def test_list_as_member(self):
        """
        We can get the payload as a member
        """
        self.activate_user("member")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_content(response)

    def test_list_as_nonmember(self):
        """
        We can NOT get the payload as a non member
        """
        self.activate_user("non_member")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
