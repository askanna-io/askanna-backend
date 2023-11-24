from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status

from core.utils.suuid import create_suuid
from storage.models import File
from tests import AskAnnaAPITestCase


class BaseStorageFileAPI(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_avatar_files, test_storage_files):
        self.users = test_users
        self.storage_files = test_storage_files
        self.avatar_files = test_avatar_files


class TestStorageFileInfo(BaseStorageFileAPI):
    def test_get_file_info(self):
        self.set_authorization(self.users["workspace_admin"])

        file_suuid = self.avatar_files["workspace_admin"].suuid
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_suuid}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == file_suuid
        assert response.data["download_info"] is not None
        assert response.data["download_info"]["type"] == "askanna"

    def test_get_file_info_db_field_name_is_empty(self):
        self.set_authorization(self.users["workspace_admin"])

        file = self.storage_files["file_private_project_with_config"]
        file.name = ""
        file.save()

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file.suuid}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == file.suuid
        assert response.data["filename"] is not None
        assert response.data["download_info"] is not None
        assert response.data["download_info"]["type"] == "askanna"

    def test_get_file_info_as_public_user_no_permissions(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(
            reverse(
                "storage-file-info",
                kwargs={"version": "v1", "suuid": self.storage_files["file_private_project_with_config"].suuid},
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_as_public_user_not_existing_suuid(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_as_anonymous_no_permissions(self):
        response = self.client.get(
            reverse(
                "storage-file-info",
                kwargs={"version": "v1", "suuid": self.storage_files["file_private_project_with_config"].suuid},
            )
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_file_info_as_anonymous_not_existing_suuid(self):
        self.client.credentials()
        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_not_existing_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_object.suuid}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == file_object.suuid
        assert response.data["download_info"] is not None
        assert response.data["download_info"]["type"] == "askanna"

        file_object.file.storage.delete(file_object.file.file.name)
        assert File.objects.filter(suuid=file_object.suuid).exists() is True
        assert file_object.file.storage.exists(file_object.file.name) is False

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_object.suuid}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_info_not_complete(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.storage_files["file_private_not_completed"]

        response = self.client.get(reverse("storage-file-info", kwargs={"version": "v1", "suuid": file_object.suuid}))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"]
            == "File upload is not completed. It is not possible to download a file that is not completed."
        )


class TestStorageFileDownload(BaseStorageFileAPI):
    def test_get_file_download(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith("attachment; filename=")
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(file_object.file.file.size)

    def test_get_file_download_set_content_disposition_type(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid}),
            HTTP_RESPONSE_CONTENT_DISPOSITION="inline",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith("inline; filename=")
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(file_object.file.file.size)

    def test_get_file_download_set_content_disposition_filename(self):
        self.set_authorization(self.users["workspace_admin"])
        file_suuid = self.avatar_files["workspace_admin"].suuid
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_suuid}),
            HTTP_RESPONSE_CONTENT_DISPOSITION="attachment; filename=test.txt",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith('attachment; filename="test.txt"')
        assert response.get("Content-Type") == str(self.avatar_files["workspace_admin"].file.file.content_type)
        assert response.get("Content-Length") == str(self.avatar_files["workspace_admin"].file.file.size)

    def test_get_file_download_set_range(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid}),
            HTTP_RANGE="bytes=0-10",
        )
        assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith("inline; filename=")
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(11)
        assert response.get("Content-Range") == f"bytes 0-10/{file_object.file.file.size}"

    def test_get_file_download_set_range_invalid_header(self):
        self.set_authorization(self.users["workspace_admin"])
        file_suuid = self.avatar_files["workspace_admin"].suuid
        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_suuid}),
            HTTP_RANGE="bytes=0-10,5-10",
        )
        assert response.status_code == status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE

    def test_get_file_download_set_width(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]

        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width=10'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith("attachment; filename=")
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") != str(file_object.file.file.size)

        assert response.get("Content-Disposition").endswith('_10x10.png"')

        image_file = ContentFile(b"".join(response.streaming_content))
        with Image.open(image_file) as image:
            assert image.size == (10, 10)

        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width=1000'
        )
        image_file = ContentFile(b"".join(response.streaming_content))
        with Image.open(image_file) as image:
            assert image.size == (1000, 1000)

        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width=10',
            HTTP_RANGE="bytes=0-10",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Range header not supported in combination with the width parameter"

        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width="a"',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Width parameter must be an integer"

        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width=-1',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Width parameter must be greater than 0"

        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width=1001',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Width parameter must be less than 1000"

        file = ContentFile(b"123", name="test.txt")
        file_object = File.objects.create(
            file=file,
            name="test.txt",
            created_for=self.users["workspace_admin"],
            created_by=self.users["workspace_admin"],
            completed_at=timezone.now(),
        )
        response = self.client.get(
            f'{reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})}?width=10',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Width parameter is only supported for image files"

        file_object.delete()

    def test_get_file_download_as_public_user_no_permissions(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(
            reverse(
                "storage-file-download",
                kwargs={"version": "v1", "suuid": self.storage_files["file_private_project_with_config"].suuid},
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_downlaod_as_public_user_not_existing_suuid(self):
        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(reverse("storage-file-download", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_download_as_anonymous_no_permissions(self):
        response = self.client.get(
            reverse(
                "storage-file-download",
                kwargs={"version": "v1", "suuid": self.storage_files["file_private_project_with_config"].suuid},
            )
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_file_download_as_anonymous_not_existing_suuid(self):
        self.client.credentials()
        response = self.client.get(reverse("storage-file-download", kwargs={"version": "v1", "suuid": create_suuid()}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_download_not_existing_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith("attachment; filename=")
        assert response.get("Content-Type") == str(file_object.file.file.content_type)
        assert response.get("Content-Length") == str(file_object.file.file.size)

        file_object.file.storage.delete(file_object.file.file.name)
        assert File.objects.filter(suuid=file_object.suuid).exists() is True
        assert file_object.file.storage.exists(file_object.file.name) is False

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_download_not_complete(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.storage_files["file_private_not_completed"]

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"]
            == "File upload is not completed. It is not possible to download a file that is not completed."
        )


class TestStorageFileDownloadPath(BaseStorageFileAPI):
    def test_get_file_download_get_file_path(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.storage_files["file_private_project_with_config"]
        test_file = Path(settings.TEST_RESOURCES_DIR / "projects/project-001/README.md")

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
            + "?file_path=README.md"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.streaming_content is not None
        assert response.get("Content-Disposition").startswith('attachment; filename="README.md"')
        assert response.get("Content-Type") == "text/plain"

        content = b"".join(response.streaming_content)
        assert response.get("Content-Length") == str(test_file.stat().st_size)
        assert response.get("Content-Length") == str(len(content))
        assert content == test_file.read_bytes()

    def test_get_file_download_get_file_path_not_complete(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.storage_files["file_private_not_completed"]

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
            + "?file_path=README.md"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"]
            == "File upload is not completed. It is not possible to download a file that is not completed."
        )

    def test_get_file_download_get_file_path_no_zip_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.avatar_files["workspace_admin"]

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
            + "?file_path=README.md"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"]
            == "The file_path parameter is only supported for zip files and the requested file is not a zip file."
        )

    def test_get_file_download_get_file_path_not_existing_file(self):
        self.set_authorization(self.users["workspace_admin"])
        file_object = self.storage_files["file_private_project_with_config"]

        response = self.client.get(
            reverse("storage-file-download", kwargs={"version": "v1", "suuid": file_object.suuid})
            + "?file_path=READ.md"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "File path 'READ.md' not found in this zip file."
