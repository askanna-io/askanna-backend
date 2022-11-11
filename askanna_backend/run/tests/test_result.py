from core.tests.base import BaseUploadTestMixin
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseRunTest


class TestResultCreateUploadAPI(BaseUploadTestMixin, BaseRunTest, APITestCase):
    """
    Test on creating result and uploading chunks
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-result",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run1"].suuid,
            },
        )
        self.register_upload_url = reverse(
            "run-result-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run1"].suuid,
            },
        )
        self.create_chunk_url = lambda artifact_object: reverse(
            "result-resultchunk-list",
            kwargs={
                "version": "v1",
                "parent_lookup_runresult__run__suuid": self.runs["run1"].suuid,
                "parent_lookup_runresult__suuid": artifact_object.get("suuid"),
            },
        )
        self.upload_chunk_url = lambda artifact_object, chunk_uuid: reverse(
            "result-resultchunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_runresult__run__suuid": self.runs["run1"].suuid,
                "parent_lookup_runresult__suuid": artifact_object.get("suuid"),
                "pk": chunk_uuid,
            },
        )
        self.finish_upload_url = lambda artifact_object: reverse(
            "run-result-finish-upload",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run1"].suuid,
                "suuid": artifact_object.get("suuid"),
            },
        )

    def check_retrieve_output(self):

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # also try the range request
        response = self.client.get(self.url, format="json", HTTP_RANGE="bytes=5-60")
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)

        # also try the range request for full file (larger than the file itself)
        response = self.client.get(self.url, format="json", HTTP_RANGE="bytes=0-100000")
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)

        # no content check as the on the fly generated zipfile is always different

    def test_create_as_admin(self):
        """
        We can create result as admin of a workspace
        """
        self.activate_user("admin")

        self.do_file_upload(
            create_url=self.register_upload_url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-result-admin.zip",
        )
        self.check_retrieve_output()

    def test_create_as_member(self):
        """
        We can create result as member of a workspace
        """
        self.activate_user("member")

        self.do_file_upload(
            create_url=self.register_upload_url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-result-admin.zip",
        )
        self.check_retrieve_output()

    def test_create_as_workspace_viewer(self):
        """
        Workspace viewers cannot create result (cannot start run)
        """
        self.activate_user("member_wv")
        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.register_upload_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-result-admin.zip",
            )
            self.check_retrieve_output()

    def test_create_as_nonmember(self):
        """
        Non members cannot create results
        """
        self.activate_user("non_member")
        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.register_upload_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-result-admin.zip",
            )
            self.check_retrieve_output()

    def test_create_as_anonymous(self):
        """
        Anonymous cannot create results
        """
        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.register_upload_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-result-admin.zip",
            )
            self.check_retrieve_output()


class TestResultDetailAPI(BaseRunTest, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-result",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run2"].suuid,
            },
        )

    def test_retrieve_as_admin(self):
        """
        We can retrieve the result as an admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(response.streaming_content), b"some result content")

    def test_retrieve_as_member(self):
        """
        We can retrieve the result as a member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(response.streaming_content), b"some result content")

    def test_retrieve_as_workspaceviewer(self):
        """
        We can retrieve the result as a member of a workspace as workspace viewer
        """
        self.activate_user("member_wv")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(response.streaming_content), b"some result content")

    def test_retrieve_as_nonmember(self):
        """
        We can NOT retrieve the result when not beeing a member of the workspace
        """
        self.activate_user("non_member")

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
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
