from django.urls import reverse
from rest_framework.test import APITestCase

from .base import BaseJobTestDef, BaseUploadTestMixin


class TestResultCreateUploadAPI(BaseUploadTestMixin, BaseJobTestDef, APITestCase):
    """
    Test on creating result and uploading chunks
    """

    def setUp(self):
        self.create_artifact_url = lambda artifact_object: reverse(
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
        self.upload_artifact_url = lambda artifact_object, chunk_uuid: reverse(
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

    def do_create_entry(self, create_url):
        return {
            "uuid": self.jobruns["run1"].output.uuid,
            "short_uuid": self.jobruns["run1"].output.short_uuid,
        }

    def test_create_as_admin(self):
        """
        We can create artifacts as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        self.do_artifact_upload(
            create_url=None,
            create_artifact_url=self.create_artifact_url,
            upload_artifact_url=self.upload_artifact_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-result-admin.zip",
        )
