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
                "parent_lookup_package__short_uuid": parent_object.get("short_uuid"),
            },
        )
        self.upload_chunk_url = lambda parent_object, chunk_uuid: reverse(
            "package-packagechunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_package__short_uuid": parent_object.get("short_uuid"),
                "pk": chunk_uuid,
            },
        )
        self.finish_upload_url = lambda parent_object: reverse(
            "package-finish-upload",
            kwargs={
                "version": "v1",
                "short_uuid": parent_object.get("short_uuid"),
            },
        )

    def test_create_as_anna(self):
        """
        Anna cannot upload because of non-membership
        """
        self.activate_user("anna")

        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.create_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-package-admin.zip",
            )

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

    def test_create_as_nonmember(self):
        """
        We can create packages as non nember of a workspace, failing the test
        """
        self.activate_user("non_member")

        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.create_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-package-admin.zip",
            )

    def test_create_as_anonymous(self):
        """
        Anonymous user just get the error
        """
        with self.assertRaises(AssertionError):
            self.do_file_upload(
                create_url=self.create_url,
                create_chunk_url=self.create_chunk_url,
                upload_chunk_url=self.upload_chunk_url,
                finish_upload_url=self.finish_upload_url,
                fileobjectname="test-package-admin.zip",
            )
