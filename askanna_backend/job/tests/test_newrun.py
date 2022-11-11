import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef


class TestJobStartAPI(BaseJobTestDef, APITestCase):

    """
    Test starting a job
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-job",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )

    def test_startjob_as_admin(self):
        """
        We can start a job as an admin
        """
        self.activate_user("admin")

        payload = {"example_payload": "startjob"}

        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "queued")
        self.assertEqual(response.data.get("message_type"), "status")

    def test_startjob_as_member(self):
        """
        We can start a job as a member
        """
        self.activate_user("member")

        payload = {"example_payload": "startjob"}

        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "queued")
        self.assertEqual(response.data.get("message_type"), "status")

    def test_startjob_as_nonmember(self):
        """
        We cannot start a job as a non-member of the jobdef
        """
        self.activate_user("non_member")

        payload = {"example_payload": "startjob"}

        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_startjob_as_anonymous(self):
        """
        We cannot start jobs as anonymous
        """
        response = self.client.post(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_startjob_with_invalid_json(self):
        """
        Starting jobs with invalid json is not possible
        in this case the json is posted as string
        """
        self.activate_user("member")

        payload = json.dumps({"example_payload": "startjob"})

        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        self.assertIn("JSON not valid, please check and try again", str(response.content))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_startjob_with_payload_in_uri(self):
        """
        We can start jobs with payload given in the uri (as get arguments)
        """
        self.activate_user("member")

        payload = {"example_payload": "startjob"}

        response = self.client.post(self.url, payload, HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_startjob_with_payload_empty(self):
        """
        We can start jobs with empty payload
        """
        self.activate_user("member")

        payload = None

        response = self.client.post(self.url, payload, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_startjob_with_payload_in_uri_empty(self):
        """
        We can start jobs with empty payload given by the uri
        """
        self.activate_user("member")

        payload = None

        response = self.client.post(self.url, payload, HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_startjob_with_askanna_agents(self):
        """
        We can start a job as different askanna-agents
        """
        self.activate_user("member")

        payload = {"example_payload": "startjob"}

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
                payload,
                format="json",
                HTTP_HOST="testserver",
                HTTP_ASKANNA_AGENT=agent,  # this variable is turned into `askanna-agent` as header
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get("status"), "queued")
            self.assertEqual(response.data.get("message_type"), "status")
            runinfo = self.client.get(
                reverse(
                    "run-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": response.data.get("suuid"),
                    },
                )
            )
            self.assertEqual(runinfo.data.get("trigger"), trigger.upper())
