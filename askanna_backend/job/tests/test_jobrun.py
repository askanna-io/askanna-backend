import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from job.models import JobDef, JobRun, JobPayload
from project.models import Project
from package.models import Package
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership, User
from workspace.models import Workspace

from .base import BaseJobTestDef


class TestJobRunListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the Jobruns
    """

    def setUp(self):
        self.url = reverse("jobrun-list", kwargs={"version": "v1"},)

    def test_list_as_admin(self):
        """
        We can list jobruns as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.jobruns.items()))

    def test_list_as_member(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.jobruns.items()))

    def test_list_as_nonmember(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We can list jobruns as member of a workspace
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobJobRunListAPI(TestJobRunListAPI):
    """
    Test to list the Jobruns
    """

    def setUp(self):
        self.url = reverse(
            "job-runs-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )

    def test_list_as_nonmember(self):
        """
        We can not list jobruns as non-member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestJobRunDetailAPI(BaseJobTestDef, APITestCase):

    """
    Test to get details of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid,},
        )

    def test_detail_as_admin(self):
        """
        We can get details of a jobrun as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )

    def test_detail_as_member(self):
        """
        We can get details of a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )

    def test_detail_as_nonmember(self):
        """
        We can NOT get details of a jobrun as non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_anonymous(self):
        """
        We can NOT get details of a jobrun as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobJobRunDetailAPI(TestJobRunDetailAPI):

    """
    Test to get details of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "job-runs-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobruns["run1"].short_uuid,
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )


class TestJobRunManifestAPI(BaseJobTestDef, APITestCase):

    """
    Test to get manifest of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "jobrun-manifest",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )

    def test_manifest_as_admin(self):
        """
        We can get the manifest for a jobrun as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manifest_as_member(self):
        """
        We can get the manifest for a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manifest_as_nonmember(self):
        """
        We can NOT get the manifest for a jobrun as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manifest_as_anonymous(self):
        """
        We can NOT get the manifest of a jborun as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobRunLogAPI(BaseJobTestDef, APITestCase):

    """
    Test to get log of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "jobrun-log",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )

    def test_log_as_admin(self):
        """
        We can get the log for a jobrun as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_member(self):
        """
        We can get the log for a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_nonmember(self):
        """
        We can NOT get the log for a jobrun as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_as_anonymous(self):
        """
        We can NOT get the log of a jborun as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobRunLogShortCutAPI(TestJobRunLogAPI):

    """
    Test to get log of a Jobrun
    Shortcut version
    """

    def setUp(self):
        self.url = reverse(
            "shortcut-jobrun-log",
            kwargs={"short_uuid": self.jobruns["run1"].short_uuid},
        )


class TestJobRunResultAPI(BaseJobTestDef, APITestCase):

    """
    Test to get result of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "shortcut-jobrun-result",
            kwargs={"short_uuid": self.jobruns["run1"].short_uuid},
        )

    def test_retrieve_as_admin(self):
        """
        We can get the result for a jobrun as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_member(self):
        """
        We can get the result for a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get the result for a jobrun as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous(self):
        """
        We can NOT get the result of a jborun as anonymous
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobRunStatusAPI(BaseJobTestDef, APITestCase):

    """
    Test to get result of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "shortcut-jobrun-status",
            kwargs={"short_uuid": self.jobruns["run1"].short_uuid},
        )

    def test_retrieve_as_admin(self):
        """
        We can get the status for a jobrun as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_member(self):
        """
        We can get the status for a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get the status for a jobrun as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous(self):
        """
        We can NOT get the status of a jborun as anonymous
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobStartAPI(BaseJobTestDef, APITestCase):

    """
    Test starting a job
    """

    def setUp(self):
        self.url = reverse("run-job", kwargs={"short_uuid": self.jobdef.short_uuid},)

    def test_startjob_as_admin(self):
        """
        We can start a job as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"example_payload": "startjob"}

        response = self.client.post(
            self.url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "queued")
        self.assertEqual(response.data.get("message_type"), "status")

    def test_startjob_as_member(self):
        """
        We can start a job as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"example_payload": "startjob"}

        response = self.client.post(
            self.url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "queued")
        self.assertEqual(response.data.get("message_type"), "status")

    def test_startjob_as_nonmember(self):
        """
        We cannot start a job as a non-member of the jobdef
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"example_payload": "startjob"}

        response = self.client.post(
            self.url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_startjob_as_anonymous(self):
        """
        We cannot start jobs as anonymous
        """
        response = self.client.post(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_startjob_with_invalid_json(self):
        """
        We can start a job as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = json.dumps({"example_payload": "startjob"})

        response = self.client.post(
            self.url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestJobPayloadAPI(BaseJobTestDef, APITestCase):

    """
    Test Getting back the payload of a job
    """

    def setUp(self):
        self.startjob_url = reverse(
            "run-job", kwargs={"short_uuid": self.jobdef.short_uuid},
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
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {
            "example_payload": "startjob",
            "multirow": True,
            "someothervar": "yes",
        }

        response = self.client.post(
            self.startjob_url, payload, format="json", HTTP_HOST="testserver"
        )
        self.jobruns["after_payload"] = JobRun.objects.get(
            short_uuid=response.data.get("run_uuid")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    def test_retrieve_as_admin(self):
        """
        We can get the payload as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_member(self):
        """
        We can get the payload as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get the payload as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_as_anonymous(self):
        """
        We can NOT get the payload as anonymous
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestJobRunPayloadAPI(TestJobPayloadAPI):

    """
    Test Getting back the payload of a jobrun
    """

    def setUp(self):
        self.startjob_url = reverse(
            "run-job", kwargs={"short_uuid": self.jobdef.short_uuid},
        )
        self.setUpPayload()
        self.url = reverse(
            "jobrun-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns[
                    "after_payload"
                ].short_uuid,
            },
        )


class TestJobPayloadRetrieveAPI(BaseJobTestDef, APITestCase):

    """
    Test Getting back the payload of a job
    """

    def setUp(self):
        self.startjob_url = reverse(
            "run-job", kwargs={"short_uuid": self.jobdef.short_uuid},
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
        self.partial_url = reverse(
            "job-payload-get-partial",
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
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {
            "example_payload": "startjob",
            "multirow": True,
            "someothervar": "yes",
        }

        response = self.client.post(
            self.startjob_url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.jobruns["after_payload"] = JobRun.objects.get(
            short_uuid=response.data.get("run_uuid")
        )
        # get the payload of this jobrun

        jobrun_payload_list_url = reverse(
            "jobrun-payload-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns[
                    "after_payload"
                ].short_uuid,
            },
        )
        response = self.client.get(
            jobrun_payload_list_url, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payload = JobPayload.objects.get(short_uuid=response.data[0]["short_uuid"])

        self.client.credentials()

    def check_content(self, response):
        self.assertEqual(response.data.get("example_payload"), "startjob")
        self.assertEqual(response.data.get("multirow"), True)
        self.assertEqual(response.data.get("someothervar"), "yes")

    def test_retrieve_as_admin(self):
        """
        We can get the payload as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_content(response)

        response = self.client.get(
            self.partial_url + "?offset=1&limit=2",
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("example_payload", str(response.content))
        self.assertIn("startjob", str(response.content))

        self.assertIn("multirow", str(response.content))
        self.assertIn("true", str(response.content))

    def test_retrieve_as_member(self):
        """
        We can get the payload as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_content(response)

        response = self.client.get(
            self.partial_url + "?offset=1&limit=2",
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("example_payload", str(response.content))
        self.assertIn("startjob", str(response.content))

        self.assertIn("multirow", str(response.content))
        self.assertIn("true", str(response.content))

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get the payload as a member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(
            self.partial_url + "?offset=1&limit=2",
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
