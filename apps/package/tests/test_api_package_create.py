import pytest
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.reverse import reverse

from package.models import Package
from storage.models import File
from storage.utils import get_md5_from_file
from tests import AskAnnaAPITestCase


class TestPackageCreateBase(AskAnnaAPITestCase):
    def setUp(self):
        super().setUp()
        self.package_url = reverse("package-list", kwargs={"version": "v1"})

    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_projects, test_memberships, mixed_format_zipfile, avatar_file):
        self.users = test_users
        self.projects = test_projects
        self.zipfile = mixed_format_zipfile
        self.avatar_file = avatar_file


class TestPackageCreate(TestPackageCreateBase):
    def test_package_create_with_file(self):
        """
        Test if create package with file work and confirm it only work for project admins and members
        """

        def package_create_with_file_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as package:
                response = self.client.post(
                    self.package_url,
                    {
                        "project_suuid": self.projects["project_private"].suuid,
                        "package": package,
                    },
                    format="multipart",
                )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("project").get("suuid") == self.projects["project_private"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"

            Package.objects.get(suuid=response.data.get("suuid")).package_file.delete_file_and_empty_directories()

            return True

        assert (
            package_create_with_file_test(user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED)
            is True
        )
        assert (
            package_create_with_file_test(user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED)
            is True
        )

        assert (
            package_create_with_file_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_create_with_file_test(user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND)
            is True
        )
        assert (
            package_create_with_file_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert package_create_with_file_test(user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED) is True

    def test_package_create_with_file_and_meta_info(self):
        """
        Test if create package with file work and confirm it only work for project admins and members
        """

        def package_create_with_file_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as package:
                response = self.client.post(
                    self.package_url,
                    {
                        "project_suuid": self.projects["project_private"].suuid,
                        "package": package,
                        "etag": self.zipfile["etag"],
                        "size": self.zipfile["size"],
                    },
                    format="multipart",
                )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("project").get("suuid") == self.projects["project_private"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"

            Package.objects.get(suuid=response.data.get("suuid")).package_file.delete_file_and_empty_directories()

            return True

        assert (
            package_create_with_file_test(user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED)
            is True
        )
        assert (
            package_create_with_file_test(user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED)
            is True
        )

        assert (
            package_create_with_file_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_create_with_file_test(user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND)
            is True
        )
        assert (
            package_create_with_file_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert package_create_with_file_test(user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED) is True

    def test_package_create_with_filename(self):
        """
        Test if create package with filename work and confirm it only work for project admins and members
        """

        def package_create_with_filename_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.package_url,
                {
                    "project_suuid": self.projects["project_private"].suuid,
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == 201
            assert response.data.get("project").get("suuid") == self.projects["project_private"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == "application/zip"

            return True

        assert (
            package_create_with_filename_test(
                user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )
        assert (
            package_create_with_filename_test(
                user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )

        assert package_create_with_filename_test(
            user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        assert package_create_with_filename_test(
            user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        assert package_create_with_filename_test(
            user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        assert package_create_with_filename_test(user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED)

    def test_package_create_with_multipart_one_part(self):
        """
        Test if create package with multipart work and confirm it only work for project admins and members
        """

        def package_create_with_multipart_one_part_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.package_url,
                {
                    "project_suuid": self.projects["project_private"].suuid,
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("project").get("suuid") == self.projects["project_private"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == "application/zip"

            package_suuid = response.data.get("suuid")
            upload_url = response.data.get("upload_info", {}).get("url")

            with self.zipfile["file"].open("rb") as part:
                response = self.client.put(
                    upload_url + "part/",
                    {
                        "part": part,
                        "part_number": 1,
                    },
                    format="multipart",
                )

            assert response.status_code == 200
            assert response.data.get("etag") == self.zipfile["etag"]

            response = self.client.post(upload_url + "complete/")

            assert response.status_code == 200
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"
            assert response.data.get("created_for").get("suuid") == package_suuid

            File.objects.get(suuid=response.data.get("suuid")).delete_file_and_empty_directories()

            return True

        assert (
            package_create_with_multipart_one_part_test(
                user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )
        assert (
            package_create_with_multipart_one_part_test(
                user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )

        assert (
            package_create_with_multipart_one_part_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_create_with_multipart_one_part_test(
                user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_create_with_multipart_one_part_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_create_with_multipart_one_part_test(
                user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED
            )
            is True
        )

    def test_package_create_with_multipart_multiple_parts(self):
        """
        Test if create package with multipart work and confirm it only work for project admins and members
        """

        def package_createwith_multipart_multiple_parts_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.package_url,
                {
                    "project_suuid": self.projects["project_private"].suuid,
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == 201
            assert response.data.get("project").get("suuid") == self.projects["project_private"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == "application/zip"

            package_suuid = response.data.get("suuid")
            upload_url = response.data.get("upload_info", {}).get("url")

            with self.zipfile["file"].open("rb") as file:
                for index, part in enumerate(
                    [
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(100),
                        file.read(),
                    ]
                ):
                    part_file = ContentFile(part)
                    response = self.client.put(
                        upload_url + "part/",
                        {
                            "part": part_file,
                            "part_number": index + 1,
                        },
                        format="multipart",
                    )

                    assert response.status_code == 200
                    assert response.data.get("etag") == get_md5_from_file(part_file)

            response = self.client.post(upload_url + "complete/")

            assert response.status_code == 200
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"
            assert response.data.get("created_for").get("suuid") == package_suuid

            File.objects.get(suuid=response.data.get("suuid")).delete_file_and_empty_directories()

            return True

        assert (
            package_createwith_multipart_multiple_parts_test(
                user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )
        assert (
            package_createwith_multipart_multiple_parts_test(
                user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )

        assert (
            package_createwith_multipart_multiple_parts_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_createwith_multipart_multiple_parts_test(
                user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_createwith_multipart_multiple_parts_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            package_createwith_multipart_multiple_parts_test(
                user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED
            )
            is True
        )


class TestPackageCreateFails(TestPackageCreateBase):
    def test_create_package_without_project_suuid(self):
        package_url = reverse("package-list", kwargs={"version": "v1"})

        self.set_authorization("workspace_admin")
        response = self.client.post(package_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field is required." in response.data["project_suuid"]

    def test_create_package_with_not_existing_project_suuid(self):
        self.set_authorization("workspace_admin")

        response = self.client.post(
            self.package_url,
            {
                "project_suuid": "1234-1234-1234-1234",
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_package_without_filename_or_package(self):
        self.set_authorization("workspace_admin")

        response = self.client.post(
            self.package_url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("detail") == "Package or filename is required"

    def test_package_create_with_file_and_wrong_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as package:
            response = self.client.post(
                self.package_url,
                {
                    "project_suuid": self.projects["project_private"].suuid,
                    "package": package,
                    "etag": 1,
                    "size": self.zipfile["size"],
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"ETag '1' does not match the ETag of the received file '{self.zipfile['etag']}'." in response.data.get(
            "etag"
        )

    def test_package_create_with_file_and_wrong_size(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as package:
            response = self.client.post(
                self.package_url,
                {
                    "project_suuid": self.projects["project_private"].suuid,
                    "package": package,
                    "size": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"Size '1' does not match the size of the received file '{self.zipfile['size']}'." in response.data.get(
            "size"
        )

    def test_package_create_with_file_and_wrong_content_type(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.post(
            self.package_url,
            {
                "project_suuid": self.projects["project_private"].suuid,
                "package": self.avatar_file,
                "size": 1,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only zip files are allowed for packages" in response.data.get("package")
