from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef, BaseUploadTestMixin


class TestResultCreateUploadAPI(BaseUploadTestMixin, BaseJobTestDef, APITestCase):
    """
    Test on creating result and uploading chunks
    """

    def setUp(self):
        self.url = reverse(
            "shortcut-jobrun-result",
            kwargs={
                "short_uuid": self.jobruns["run1"].short_uuid,
            },
        )
        self.create_chunk_url = lambda artifact_object: reverse(
            "result-resultchunk-list",
            kwargs={
                "version": "v1",
                "parent_lookup_joboutput__jobrun__short_uuid": self.jobruns[
                    "run1"
                ].short_uuid,
                "parent_lookup_joboutput__short_uuid": artifact_object.get(
                    "short_uuid"
                ),
            },
        )
        self.upload_chunk_url = lambda artifact_object, chunk_uuid: reverse(
            "result-resultchunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_joboutput__jobrun__short_uuid": self.jobruns[
                    "run1"
                ].short_uuid,
                "parent_lookup_joboutput__short_uuid": artifact_object.get(
                    "short_uuid"
                ),
                "pk": chunk_uuid,
            },
        )
        self.finish_upload_url = lambda artifact_object: reverse(
            "jobrun-result-finish-upload",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns["run1"].short_uuid,
                "short_uuid": artifact_object.get("short_uuid"),
            },
        )

    def do_create_entry(self, create_url, filename=None, filesize=None):
        return {
            "uuid": self.jobruns["run1"].output.uuid,
            "short_uuid": self.jobruns["run1"].output.short_uuid,
        }

    def check_retrieve_output(self):

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # also try the range request
        response = self.client.get(self.url, format="json", HTTP_RANGE="bytes=5-60")
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)

        # no content check as the on the fly generated zipfile is always different

    def test_create_as_admin(self):
        """
        We can create result as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        self.do_file_upload(
            create_url=None,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-result-admin.zip",
        )
        self.check_retrieve_output()


class TestResultDetaiAPI(BaseJobTestDef, APITestCase):
    def setUp(self):
        self.url = reverse(
            "shortcut-jobrun-result",
            kwargs={
                "short_uuid": self.jobruns["run1"].short_uuid,
            },
        )

    def test_options_header(self):
        """
        Test wether we can get an options request
        """

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.options(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["accept-ranges"], "bytes")

    def test_retrieve_as_admin(self):
        """
        We can retrieve the result as an admin of a workspace
        """

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"")

    def test_retrieve_as_member(self):
        """
        We can retrieve the result as a member of a workspace
        """

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"")

    def test_retrieve_as_nonmember(self):
        """
        We can NOT retrieve the result when not beeing a member of the workspace
        """

        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the result as anonymous user
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
