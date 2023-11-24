import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.reverse import reverse

from storage.models import File
from tests import AskAnnaAPITestCase


class BaseStorageFileAPI(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_storage_files, mixed_format_zipfile, avatar_file):
        self.users = test_users
        self.files = test_storage_files
        self.zipfile = mixed_format_zipfile
        self.avatar_file = avatar_file

    def get_upload_part_url(self, suuid):
        return reverse(
            "storage-file-upload-part",
            kwargs={
                "version": "v1",
                "suuid": suuid,
            },
        )

    def get_upload_complete_url(self, suuid):
        return reverse(
            "storage-file-upload-complete",
            kwargs={
                "version": "v1",
                "suuid": suuid,
            },
        )

    def get_upload_abort_url(self, suuid):
        return reverse(
            "storage-file-upload-abort",
            kwargs={
                "version": "v1",
                "suuid": suuid,
            },
        )


class TestStorageFileUploadPart(BaseStorageFileAPI):
    def test_upload_part(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("etag") == self.zipfile["etag"]
        assert self.files["file_private_not_completed"].part_filenames == [
            f"{self.files['file_private_not_completed'].suuid}_part_00001.part"
        ]
        assert self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + f"/{self.files['file_private_not_completed'].suuid}_part_00001.part"
        )

    def test_upload_part_with_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                    "etag": self.zipfile["etag"],
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("etag") == self.zipfile["etag"]
        assert self.files["file_private_not_completed"].part_filenames == [
            f"{self.files['file_private_not_completed'].suuid}_part_00001.part"
        ]
        assert self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + f"/{self.files['file_private_not_completed'].suuid}_part_00001.part"
        )

    def test_upload_part_with_wrong_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                    "etag": "1",
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"ETag '1' is not equal to the ETag of the part received '{self.zipfile['etag']}'" in response.data.get(
            "etag"
        )

    def test_upload_part_twice(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.put(
            self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
            {
                "part": self.avatar_file,
                "part_number": 1,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("etag") != self.zipfile["etag"]
        assert self.files["file_private_not_completed"].part_filenames == [
            f"{self.files['file_private_not_completed'].suuid}_part_00001.part"
        ]
        assert self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + "/"
            + self.files["file_private_not_completed"].part_filenames[0]
        )

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("etag") == self.zipfile["etag"]
        assert self.files["file_private_not_completed"].part_filenames == [
            f"{self.files['file_private_not_completed'].suuid}_part_00001.part"
        ]
        assert self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + f"/{self.files['file_private_not_completed'].suuid}_part_00001.part"
        )

    def test_upload_part_with_invalid_part_number(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": -1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("part_number") is not None

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 100001,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("part_number") is not None

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": "a",
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("part_number") is not None

    def test_upload_part_for_completed_file(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_project_with_config"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data.get("detail") == "File upload is already completed and uploading new parts is not allowed."
        )


class TestStorageFileUploadComplete(BaseStorageFileAPI):
    def _create_upload_part(self):
        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("etag") == self.zipfile["etag"]
        assert self.files["file_private_not_completed"].part_filenames == [
            f"{self.files['file_private_not_completed'].suuid}_part_00001.part"
        ]
        assert self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + f"/{self.files['file_private_not_completed'].suuid}_part_00001.part"
        )

    def test_upload_complete(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("filename") == "mixed_format_archive.zip"
        assert response.data.get("size") == self.zipfile["size"]
        assert response.data.get("etag") == self.zipfile["etag"]
        assert response.data.get("content_type") == "application/zip"

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "etag": self.zipfile["etag"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("filename") == "mixed_format_archive.zip"
        assert response.data.get("size") == self.zipfile["size"]
        assert response.data.get("etag") == self.zipfile["etag"]
        assert response.data.get("content_type") == "application/zip"

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_wrong_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "etag": 1,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            f"ETag '1' is not equal to the ETag '{self.zipfile['etag']}' of the file received."
            in response.data.get("etag")
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_wrong_instance_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        self.files["file_private_not_completed"].etag = "2"
        self.files["file_private_not_completed"].save()
        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            f"ETag '2' is not equal to the ETag '{self.zipfile['etag']}' of the file received."
            in response.data.get("etag")
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_wrong_instance_size(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        self.files["file_private_not_completed"].size = 1
        self.files["file_private_not_completed"].save()
        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            f"Size '1' is not equal to the size '{self.zipfile['size']}' of the file received."
            in response.data.get("size")
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_wrong_instance_content_type(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        self.files["file_private_not_completed"].content_type = "does_not_exist"
        self.files["file_private_not_completed"].save()
        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            f"Content type 'does_not_exist' is not equal to the content type '{self.zipfile['content_type']}' of the "
            "file received." in response.data.get("content_type")
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_parts(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "parts": [
                    {
                        "part_number": 1,
                        "etag": self.zipfile["etag"],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("filename") == "mixed_format_archive.zip"
        assert response.data.get("size") == self.zipfile["size"]
        assert response.data.get("etag") == self.zipfile["etag"]
        assert response.data.get("content_type") == "application/zip"

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_parts_with_wrong_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "parts": [
                    {
                        "part_number": 1,
                        "etag": 1,
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            f"ETag '1' for part 1 is not equal to the ETag '{self.zipfile['etag']}' of the file part received."
            in response.data.get("parts")
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_parts_with_missing_part_number(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "parts": [
                    {
                        "part_number": 2,
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Part 2 does not exist in the storage system" in response.data.get("parts")

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_parts_with_invalid_part_number(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "parts": [
                    {
                        "part_number": 0,
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Ensure this value is greater than or equal to 1." in response.data.get("parts").get(0).get(
            "part_number"
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_parts_with_too_many_parts(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
            {
                "parts": [
                    {
                        "part_number": 1,
                    },
                    {
                        "part_number": 2,
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Expected 1 parts, but received 2 parts" in response.data.get("parts")

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_with_locked_file(self):
        self.set_authorization(self.users["workspace_admin"])

        self._create_upload_part()

        cache.set(f"storage.File:{self.files['file_private_not_completed'].suuid}:lock", True)
        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
        )
        cache.delete(f"storage.File:{self.files['file_private_not_completed'].suuid}:lock")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data.get("detail")
            == "File is locked by another process and upload cannot be completed at this moment."
        )

        File.objects.get(suuid=self.files["file_private_not_completed"].suuid).delete_file_and_empty_directories()

    def test_upload_complete_for_completed_file(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_project_with_config"].suuid),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data.get("detail") == "File upload is already completed and uploading new parts is not allowed."
        )

    def test_upload_complete_with_no_uploaded_parts(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.post(
            self.get_upload_complete_url(self.files["file_private_not_completed"].suuid),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("detail") == "No uploaded parts found"


class TestStorageFileUploadAbort(BaseStorageFileAPI):
    def test_upload_abort(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as part:
            response = self.client.put(
                self.get_upload_part_url(self.files["file_private_not_completed"].suuid),
                {
                    "part": part,
                    "part_number": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("etag") == self.zipfile["etag"]
        assert self.files["file_private_not_completed"].part_filenames == [
            f"{self.files['file_private_not_completed'].suuid}_part_00001.part"
        ]
        assert self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + f"/{self.files['file_private_not_completed'].suuid}_part_00001.part"
        )

        response = self.client.post(
            self.get_upload_abort_url(self.files["file_private_not_completed"].suuid),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        with pytest.raises(File.DoesNotExist):
            File.objects.get(suuid=self.files["file_private_not_completed"].suuid)
        assert not self.files["file_private_not_completed"].storage.exists(
            self.files["file_private_not_completed"].upload_to
            + f"/{self.files['file_private_not_completed'].suuid}_part_00001.part"
        )

    def test_upload_abort_completed_file(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.post(
            self.get_upload_abort_url(self.files["file_private_project_with_config"].suuid),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data.get("detail")
            == "Upload is already completed. It is not possible to abort an upload that is completed."
        )

    def test_upload_abort_locked_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_suuid = self.files["file_private_not_completed"].suuid

        cache.set(f"storage.File:{file_suuid}:lock", True)
        response = self.client.post(
            self.get_upload_abort_url(file_suuid),
        )
        cache.delete(f"storage.File:{file_suuid}:lock")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data.get("detail")
            == "File is locked by another process and upload cannot be aborted at this moment."
        )
