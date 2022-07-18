# -*- coding: utf-8 -*-
import hashlib
import io
import re

import pytest
from django.conf import settings
from django.urls import re_path, reverse
from django.views.static import serve
from rest_framework import status
from rest_framework.test import APITestCase

import config.urls

from .base import BaseJobTestDef, BaseUploadTestMixin

pytestmark = pytest.mark.django_db


class TestArtifactListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the artifacts
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-artifact-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns["run1"].short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list artifacts as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_member(self):
        """
        We can list artifacts as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_nonmember(self):
        """
        We can NOT list artifacts as non-member of a workspace
        Will get an empty list
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_as_anonymous(self):
        """
        We can NOT list artifacts as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestArtifactDetailAPI(BaseJobTestDef, APITestCase):
    """
    Test to get a detail from  the artifacts
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-artifact-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns["run1"].short_uuid,
                "short_uuid": self.artifact.short_uuid,
            },
        )

    def test_retrieve_as_admin(self):
        """
        We can get artifacts as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_member(self):
        """
        We can get artifacts as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get artifacts as non-member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous(self):
        """
        We can NOT get artifacts as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestShortcutArtifactAPI(BaseJobTestDef, APITestCase):
    """
    Test get artifact via the shortcut
    """

    @pytest.fixture(autouse=True)
    def setup_cdn(self, settings):
        settings.ASKANNA_CDN_URL = "http://testserver"

    def setUp(self):
        """
        The short-uuid is from a job-run where the artifact is generated from
        """
        super().setUp()
        self.url = reverse(
            "shortcut-artifact",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )
        self.url_no_artifact = reverse(
            "shortcut-artifact",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run2"].short_uuid},
        )

        self.setUpUrls()

    def setUpUrls(self):
        self.original_urls = config.urls.urlpatterns
        config.urls.urlpatterns += [
            re_path(
                r"^%s(?P<path>.*)$" % re.escape("/files/".lstrip("/")),
                serve,
                kwargs={"document_root": str(settings.ROOT_DIR("storage_root"))},
            )
        ]

    def tearDown(self):
        super().tearDown()
        config.urls.urlpatterns = self.original_urls

    def check_artifact(self, url):
        fileresponse = self.client.get(url)
        self.assertEqual(fileresponse.status_code, status.HTTP_200_OK)

        downloaded_file = io.BytesIO(fileresponse.getvalue())
        # download the artifact and compare with our test file
        self.assertEqual(
            hashlib.sha256(self.file_to_bytes(downloaded_file)).digest(),
            hashlib.sha256(
                self.file_to_bytes(
                    open(
                        settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip"),
                        "rb",
                    )
                )
            ).digest(),
        )

    def test_retrieve_as_admin(self):
        """
        We can get artifacts as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.check_artifact(response.url)

    def test_retrieve_as_member(self):
        """
        We can get artifacts as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.check_artifact(response.url)

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get artifacts as non-member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous(self):
        """
        We can NOT get artifacts as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # test for not found, run2 doesn't have an artifact

    def test_retrieve_as_admin_not_found(self):
        """
        We can get artifacts as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url_no_artifact,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_member_not_found(self):
        """
        We can get artifacts as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url_no_artifact,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_nonmember_not_found(self):
        """
        We can NOT get artifacts as non-member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url_no_artifact,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous_not_found(self):
        """
        We can NOT get artifacts as anonymous
        """
        response = self.client.get(
            self.url_no_artifact,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestArtifactCreateUploadAPI(BaseUploadTestMixin, BaseJobTestDef, APITestCase):
    """
    Test on creating artifacts and uploading chunks
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-artifact-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns["run1"].short_uuid,
            },
        )
        self.create_chunk_url = lambda artifact_object: reverse(
            "artifact-artifactchunk-list",
            kwargs={
                "version": "v1",
                "parent_lookup_artifact__jobrun__short_uuid": self.jobruns["run1"].short_uuid,
                "parent_lookup_artifact__short_uuid": artifact_object.get("short_uuid"),
            },
        )
        self.upload_chunk_url = lambda artifact_object, chunk_uuid: reverse(
            "artifact-artifactchunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_artifact__jobrun__short_uuid": self.jobruns["run1"].short_uuid,
                "parent_lookup_artifact__short_uuid": artifact_object.get("short_uuid"),
                "pk": chunk_uuid,
            },
        )
        self.finish_upload_url = lambda artifact_object: reverse(
            "run-artifact-finish-upload",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.jobruns["run1"].short_uuid,
                "short_uuid": artifact_object.get("short_uuid"),
            },
        )

    def test_create_as_admin(self):
        """
        We can create artifacts as admin of a workspace
        """
        self.activate_user("admin")

        self.do_file_upload(
            create_url=self.url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-artifact-admin.zip",
        )

    def test_create_as_member(self):
        """
        We can create artifacts as admin of a workspace
        """
        self.activate_user("member")

        self.do_file_upload(
            create_url=self.url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-artifact-admin.zip",
        )

    def test_create_as_workspace_viewer(self):
        """
        Workspace viewers cannot create artifacts
        """
        self.activate_user("member_wv")

        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-artifact-admin.zip",
            )

    def test_create_as_nonmember(self):
        """
        Non members cannot create artifacts
        """
        self.activate_user("non_member")

        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-artifact-admin.zip",
            )

    def test_create_as_anonymous(self):
        """
        Anonymous users cannot create artifacts
        """
        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-artifact-admin.zip",
            )
