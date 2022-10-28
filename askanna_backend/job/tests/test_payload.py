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
            kwargs={"version": "v1", "short_uuid": self.jobdef.short_uuid},
        )
        self.url = reverse(
            "job-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
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
        self.runs["after_payload"] = Run.objects.get(short_uuid=response.data.get("short_uuid"))
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
            kwargs={"version": "v1", "short_uuid": self.jobdef.short_uuid},
        )
        self.setUpPayload()
        self.url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__short_uuid": self.runs["after_payload"].short_uuid,
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
            kwargs={"version": "v1", "short_uuid": self.jobdef.short_uuid},
        )
        self.setUpPayload()
        self.url = reverse(
            "job-payload-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
                "short_uuid": self.payload.short_uuid,
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

        self.runs["after_payload"] = Run.objects.get(short_uuid=response.data.get("short_uuid"))
        # get the payload of this run

        run_payload_list_url = reverse(
            "run-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__short_uuid": self.runs["after_payload"].short_uuid,
            },
        )
        response = self.client.get(run_payload_list_url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payload = JobPayload.objects.get(short_uuid=response.data[0]["short_uuid"])

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
