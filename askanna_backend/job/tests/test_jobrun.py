# -*- coding: utf-8 -*-
import json
from dateutil.parser import parse as date_parse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from job.models import JobRun, JobPayload

from .base import BaseJobTestDef


class TestJobRunListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the Jobruns
    """

    def setUp(self):
        self.url = reverse(
            "jobrun-list",
            kwargs={"version": "v1"},
        )

    def test_list_as_admin(self):
        """
        We can list jobruns as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_member(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_nonmember(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We can list jobruns as member of a workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_member_filter_by_job(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        filter_params = {"job": self.jobdef.short_uuid}
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_member_filter_by_jobs(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        filter_params = {
            "job": ",".join([self.jobdef.short_uuid, self.jobdef2.short_uuid])
        }
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_as_member_filter_by_project(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)


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

    def test_list_as_member(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_nonmember(self):
        """
        We can not list jobruns as non-member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_member_filter_by_job(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        filter_params = {"job": self.jobdef.short_uuid}
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_member_filter_by_jobs(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        filter_params = {
            "job": ",".join([self.jobdef.short_uuid, self.jobdef2.short_uuid])
        }
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_member_filter_by_project(self):
        """
        We can list jobruns as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class TestJobRunDetailAPI(BaseJobTestDef, APITestCase):

    """
    Test to get details of a Jobrun
    """

    def setUp(self):
        self.url = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )
        self.url_run2 = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run2"].short_uuid},
        )
        self.url_other_workspace = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run3"].short_uuid},
        )

    def test_detail_as_admin(self):
        """
        We can get details of a jobrun as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
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

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )

    def test_detail_as_member_other_run(self):
        """
        We can get details of a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url_run2,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run2"].short_uuid
        )

    def test_detail_as_member_changed_membername(self):
        """
        We can get details of a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )
        self.assertEqual(response.data.get("owner").get("name"), "membername")

        # now change membername to new membername
        self.memberA_member.name = "new membername"
        self.memberA_member.save()

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )
        self.assertEqual(response.data.get("owner").get("name"), "new membername")

        # now change back new membername to membername
        self.memberA_member.name = "membername"
        self.memberA_member.save()

    def test_detail_as_member_workspacemembername_different_in_other_workspace(self):
        """
        We can get details of a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        # first visit 1st workspace
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )
        self.assertEqual(response.data.get("owner").get("name"), "membername")

        # then visit 2nd workspace
        response = self.client.get(
            self.url_other_workspace,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run3"].short_uuid
        )
        self.assertEqual(response.data.get("owner").get("name"), "membername2")

    def test_detail_as_nonmember(self):
        """
        We can NOT get details of a jobrun as non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_anonymous(self):
        """
        We can NOT get details of a jobrun as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
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
        self.url_run2 = reverse(
            "job-runs-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobruns["run2"].short_uuid,
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )
        self.url_other_workspace = reverse(
            "job-runs-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobruns["run3"].short_uuid,
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )

    def test_detail_as_member_workspacemembername_different_in_other_workspace(self):
        """
        This detail page is not applicable when in jobjob detail
        """
        pass


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

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manifest_as_member(self):
        """
        We can get the manifest for a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manifest_as_nonmember(self):
        """
        We can NOT get the manifest for a jobrun as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manifest_as_anonymous(self):
        """
        We can NOT get the manifest of a jborun as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manifest_as_member_no_config_found(self):
        """
        There is no askanna.yml found
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("AskAnna could not find the file:", str(response.content))

    def test_manifest_as_member_no_job_not_found(self):
        """
        The job is not found in askanna.yml
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        url = reverse(
            "jobrun-manifest",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run3"].short_uuid},
        )

        response = self.client.get(
            url,
            format="json",
        )
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("AskAnna could not start the job", str(response.content))

    def test_manifest_as_member_correct_job(self):
        """
        The job is not found in askanna.yml
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        url = reverse(
            "jobrun-manifest",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run4"].short_uuid},
        )

        response = self.client.get(
            url,
            format="json",
        )
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("python my_script.py", str(response.content))


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

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_member(self):
        """
        We can get the log for a jobrun as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_as_nonmember(self):
        """
        We can NOT get the log for a jobrun as a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_as_anonymous(self):
        """
        We can NOT get the log of a jborun as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
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
        self.url = reverse(
            "run-job",
            kwargs={"short_uuid": self.jobdef.short_uuid},
        )

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
        Starting jobs with invalid json is not possible
        in this case the json is posted as string
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = json.dumps({"example_payload": "startjob"})

        response = self.client.post(
            self.url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertIn(
            "JSON not valid, please check and try again", str(response.content)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_startjob_with_payload_in_uri(self):
        """
        We can start jobs with payload given in the uri (as get arguments)
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = {"example_payload": "startjob"}

        response = self.client.post(self.url, payload, HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_startjob_with_payload_empty(self):
        """
        We can start jobs with empty payload
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = None

        response = self.client.post(
            self.url, payload, format="json", HTTP_HOST="testserver"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_startjob_with_payload_in_uri_empty(self):
        """
        We can start jobs with empty payload given by the uri
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        payload = None

        response = self.client.post(self.url, payload, HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestJobPayloadAPI(BaseJobTestDef, APITestCase):

    """
    Test Getting back the payload of a job
    """

    def setUp(self):
        self.startjob_url = reverse(
            "run-job",
            kwargs={"short_uuid": self.jobdef.short_uuid},
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
            short_uuid=response.data.get("short_uuid")
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
            "run-job",
            kwargs={"short_uuid": self.jobdef.short_uuid},
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
            "run-job",
            kwargs={"short_uuid": self.jobdef.short_uuid},
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
            short_uuid=response.data.get("short_uuid")
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


class TestJobRunDetailUpdateAPI(BaseJobTestDef, APITestCase):
    """
    Test whether we can change the name and description of the run object
    """

    def setUp(self):
        self.url = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )
        self.url_run2 = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run2"].short_uuid},
        )
        self.url_other_workspace = reverse(
            "jobrun-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run3"].short_uuid},
        )

    def run_test(self, token):

        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        initial_response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            initial_response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )
        self.assertEqual(initial_response.data.get("name"), self.jobruns["run1"].name)
        self.assertEqual(
            date_parse(initial_response.data.get("modified")),
            self.jobruns["run1"].modified,
        )
        self.assertEqual(
            initial_response.data.get("description"), self.jobruns["run1"].description
        )

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data.get("short_uuid") == self.jobruns["run1"].short_uuid
        )
        self.assertEqual(response.data.get("name"), "new name")
        self.assertEqual(response.data.get("description"), "new description")
        # make sure that with this update of name and description we don't modify the
        # modified datetime of the run.
        self.assertEqual(
            date_parse(response.data.get("modified")),
            self.jobruns["run1"].modified,
        )

    def test_update_as_admin(self):
        """
        We can update name and detail of the run as admin
        """
        token = self.users["admin"].auth_token
        self.run_test(token)

    def test_update_as_member(self):
        """
        We can update name and detail of the run as member
        """
        token = self.users["user"].auth_token
        self.run_test(token)

    def test_update_as_nonmember(self):
        """
        We can NOT update name and detail of the run as non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
