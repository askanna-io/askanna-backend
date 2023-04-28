import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from core.tests.base import BaseUploadTestMixin
from job.tests.base import BaseJobTestDef


class TestPackageCreateUploadAPI(BaseUploadTestMixin, BaseJobTestDef, APITestCase):
    """
    Test on creating packages and uploading chunks
    """

    def setUp(self):
        super().setUp()

        self.create_url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )
        self.create_chunk_url = lambda parent_object: reverse(
            "package-packagechunk-list",
            kwargs={
                "version": "v1",
                "parent_lookup_package__suuid": parent_object.get("suuid"),
            },
        )
        self.upload_chunk_url = lambda parent_object, chunk_uuid: reverse(
            "package-packagechunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_package__suuid": parent_object.get("suuid"),
                "pk": chunk_uuid,
            },
        )
        self.finish_upload_url = lambda parent_object: reverse(
            "package-finish-upload",
            kwargs={
                "version": "v1",
                "suuid": parent_object.get("suuid"),
            },
        )

    def test_create_as_askanna_admin(self):
        """
        An AskAnna admin cannot upload because of non-membership
        """
        self.activate_user("anna")
        with pytest.raises(AssertionError) as excinfo:
            self.do_file_upload(
                create_url=self.create_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-package-admin.zip",
            )

        assert "403" == str(excinfo.value)

    def test_create_as_admin(self):
        """
        We can create packages as admin of a workspace
        """
        self.activate_user("admin")
        self.do_file_upload(
            create_url=self.create_url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-package-admin.zip",
        )

    def test_create_as_member(self):
        """
        We can create packages as a regular user of a workspace
        """
        self.activate_user("member")
        self.do_file_upload(
            create_url=self.create_url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-package-admin.zip",
        )

    def test_create_as_non_member(self):
        """
        We cannot create packages as non nember of a workspace
        """
        self.activate_user("non_member")
        with pytest.raises(AssertionError) as excinfo:
            self.do_file_upload(
                create_url=self.create_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-package-admin.zip",
            )
        assert "403" == str(excinfo.value)

    def test_create_as_anonymous(self):
        """
        We cannot create packages as an anonymous viewer
        """
        with pytest.raises(AssertionError) as excinfo:
            self.do_file_upload(
                create_url=self.create_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-package-admin.zip",
            )
        assert "401" == str(excinfo.value)
