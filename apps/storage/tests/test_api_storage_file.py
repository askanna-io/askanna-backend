import pytest
from django.urls import reverse
from rest_framework import status

from core.utils.suuid import create_suuid
from storage.models import File
from tests import AskAnnaAPITestCASE


class BaseStorageFileAPI(AskAnnaAPITestCASE):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_avatar_files):
        self.users = test_users
        self.avatar_files = test_avatar_files


class TestStorageFileInfo(BaseStorageFileAPI):
    def test_get_file_info(self):
        self.set_authorization(self.users["workspace_admin"])
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_suuid}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == file_suuid  # type: ignore
        assert response.data["download_info"] is not None  # type: ignore
        assert response.data["download_info"]["type"] == "askanna"  # type: ignore

    def test_get_file_info_db_field_name_is_empty(self):
        self.set_authorization(self.users["workspace_admin"])
        file = self.avatar_files["workspace_admin"].first()
        file.name = ""
        file.save()

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file.suuid}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == file.suuid  # type: ignore
        assert response.data["filename"] is not None  # type: ignore
        assert response.data["download_info"] is not None  # type: ignore
        assert response.data["download_info"]["type"] == "askanna"  # type: ignore

    def test_get_file_info_as_public_user_no_permissions(self):
        self.set_authorization(self.users["no_workspace_member"])
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_suuid}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_as_public_user_not_existing_suuid(self):
        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_as_anonymous_no_permissions(self):
        self.client.credentials()  # type: ignore
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_suuid}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_as_anonymous_not_existing_suuid(self):
        self.client.credentials()  # type: ignore
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_not_existing_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"].first()

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_object.suuid}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == file_object.suuid  # type: ignore
        assert response.data["download_info"] is not None  # type: ignore
        assert response.data["download_info"]["type"] == "askanna"  # type: ignore

        file_object.file.storage.delete(file_object.file.file.name)
        assert File.objects.filter(suuid=file_object.suuid).exists() is True
        assert file_object.file.storage.exists(file_object.file.name) is False

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_object.suuid}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStorageFileDownload(BaseStorageFileAPI):
    def test_get_file_download(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"].first()

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None  # type: ignore
        assert response.get("Content-Disposition").startswith("attachment; filename=")  # type: ignore
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(file_object.file.file.size)

    def test_get_file_download_set_content_disposition_type(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"].first()
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid}),
            HTTP_RESPONSE_CONTENT_DISPOSITION="inline",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None  # type: ignore
        assert response.get("Content-Disposition").startswith("inline; filename=")  # type: ignore
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(file_object.file.file.size)

    def test_get_file_download_set_content_disposition_filename(self):
        self.set_authorization(self.users["workspace_admin"])
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_suuid}),
            HTTP_RESPONSE_CONTENT_DISPOSITION="attachment; filename=test.txt",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None  # type: ignore
        assert response.get("Content-Disposition").startswith('attachment; filename="test.txt"')  # type: ignore
        assert response.get("Content-Type") == str(self.avatar_files["workspace_admin"].first().file.file.content_type)
        assert response.get("Content-Length") == str(self.avatar_files["workspace_admin"].first().file.file.size)

    def test_get_file_download_set_range(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"].first()
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid}),
            HTTP_RANGE="bytes=0-10",
        )
        assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
        assert response.streaming_content is not None  # type: ignore
        assert response.get("Content-Disposition").startswith("inline; filename=")  # type: ignore
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(11)
        assert response.get("Content-Range") == f"bytes 0-10/{file_object.file.file.size}"

    def test_get_file_download_set_range_invalid_header(self):
        self.set_authorization(self.users["workspace_admin"])
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_suuid}),
            HTTP_RANGE="bytes=0-10,5-10",
        )
        assert response.status_code == status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE

    def test_get_file_download_as_public_user_no_permissions(self):
        self.set_authorization(self.users["no_workspace_member"])
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_suuid}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_downlaod_as_public_user_not_existing_suuid(self):
        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(reverse("storage-file-download", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_download_as_anonymous_no_permissions(self):
        self.client.credentials()  # type: ignore
        file_suuid = self.avatar_files["workspace_admin"].first().suuid
        response = self.client.get(reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_suuid}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_download_as_anonymous_not_existing_suuid(self):
        self.client.credentials()  # type: ignore
        response = self.client.get(reverse("storage-file-download", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_download_not_existing_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"].first()

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None  # type: ignore
        assert response.get("Content-Disposition").startswith("attachment; filename=")  # type: ignore
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(file_object.file.file.size)

        file_object.file.storage.delete(file_object.file.file.name)
        assert File.objects.filter(suuid=file_object.suuid).exists() is True
        assert file_object.file.storage.exists(file_object.file.name) is False

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
