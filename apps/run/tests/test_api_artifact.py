import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status

from run.models import RunArtifact
from run.tests.base import BaseAPITestRun
from storage.models import File
from storage.utils.file import get_md5_from_file


class TestArtifactDetailAPI(BaseAPITestRun):
    """
    Test to get a detail from  the artifacts
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-artifact-detail",
            kwargs={
                "version": "v1",
                "suuid": self.artifacts["artifact_1"].suuid,
            },
        )

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot get artifacts as an AskAnna admin who is not a member of a workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_admin(self):
        """
        We can get artifacts as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.artifacts["artifact_1"].suuid
        assert response.data["size"] == self.artifacts["artifact_1"].artifact_file.size

    def test_retrieve_as_member(self):
        """
        We can get artifacts as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.artifacts["artifact_1"].suuid
        assert response.data["size"] == self.artifacts["artifact_1"].artifact_file.size

    def test_retrieve_as_viewer(self):
        """
        We can get artifacts as viewer of a workspace
        """
        self.set_authorization(self.users["workspace_viewer"])
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.artifacts["artifact_1"].suuid
        assert response.data["size"] == self.artifacts["artifact_1"].artifact_file.size

    def test_retrieve_as_non_member(self):
        """
        We cannot get artifacts as non-member of a workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_anonymous(self):
        """
        We cannot get artifacts as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestArtifactUpdateAPI(BaseAPITestRun):
    def test_artifact_update(self):
        """
        Test if artifact update work and confirm it only work for project admins and members
        """

        def artifact_update_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.patch(
                reverse(
                    "run-artifact-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": self.artifacts["artifact_1"].suuid,
                    },
                ),
                {"description": "a new description"},
            )

            if expected_status_code != status.HTTP_200_OK:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_200_OK

            assert response.data["suuid"] == self.artifacts["artifact_1"].suuid
            assert response.data.get("filename") == self.artifacts["artifact_1"].artifact_file.name
            assert response.data.get("size") == self.artifacts["artifact_1"].artifact_file.size

            assert response.data.get("description") != self.artifacts["artifact_1"].artifact_file.description
            assert self.artifacts["artifact_1"].artifact_file.description != "a new description"
            assert response.data.get("description") == "a new description"

            return True

        assert artifact_update_test(user_name="workspace_admin", expected_status_code=status.HTTP_200_OK)
        assert artifact_update_test(user_name="workspace_member", expected_status_code=status.HTTP_200_OK)

        assert artifact_update_test(user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert artifact_update_test(user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert artifact_update_test(user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert artifact_update_test(user_name=None, expected_status_code=status.HTTP_404_NOT_FOUND)


class TestArtifactCreateAPI(BaseAPITestRun):
    """
    Test on creating artifacts and uploading parts
    """

    def setUp(self):
        super().setUp()
        self.artifact_url = reverse("run-artifact-list", kwargs={"version": "v1"})

    @pytest.fixture(autouse=True)
    def _set_artifact_fixtures(self, mixed_format_zipfile, avatar_file):
        self.zipfile = mixed_format_zipfile
        self.avatar_file = avatar_file

    def test_artifact_create_with_file(self):
        """
        Test if create artifact with file work and confirm it only work for project admins and members
        """

        def artifact_create_with_file_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as artifact:
                response = self.client.post(
                    self.artifact_url,
                    {
                        "run_suuid": self.runs["run_1"].suuid,
                        "artifact": artifact,
                    },
                    format="multipart",
                )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("project").get("suuid") == self.runs["run_1"].jobdef.project.suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"

            RunArtifact.objects.get(suuid=response.data.get("suuid")).artifact_file.delete_file_and_empty_directories()

            return True

        assert (
            artifact_create_with_file_test(user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED)
            is True
        )
        assert (
            artifact_create_with_file_test(user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED)
            is True
        )

        assert (
            artifact_create_with_file_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_file_test(
                user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_file_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_file_test(user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED) is True
        )

    def test_artifact_create_with_file_and_meta_info(self):
        """
        Test if create artifact with file work and confirm it only work for project admins and members
        """

        def artifact_create_with_file_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as artifact:
                response = self.client.post(
                    self.artifact_url,
                    {
                        "run_suuid": self.runs["run_1"].suuid,
                        "artifact": artifact,
                        "etag": self.zipfile["etag"],
                        "size": self.zipfile["size"],
                    },
                    format="multipart",
                )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("project").get("suuid") == self.runs["run_1"].jobdef.project.suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"

            RunArtifact.objects.get(suuid=response.data.get("suuid")).artifact_file.delete_file_and_empty_directories()

            return True

        assert (
            artifact_create_with_file_test(user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED)
            is True
        )
        assert (
            artifact_create_with_file_test(user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED)
            is True
        )

        assert (
            artifact_create_with_file_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_file_test(
                user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_file_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_file_test(user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED) is True
        )

    def test_artifact_create_with_filename(self):
        """
        Test if create artifact with filename work and confirm it only work for project admins and members
        """

        def artifact_create_with_filename_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.artifact_url,
                {
                    "run_suuid": self.runs["run_1"].suuid,
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == 201
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("project").get("suuid") == self.runs["run_1"].jobdef.project.suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == "application/zip"

            return True

        assert (
            artifact_create_with_filename_test(
                user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )
        assert (
            artifact_create_with_filename_test(
                user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )

        assert artifact_create_with_filename_test(
            user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        assert artifact_create_with_filename_test(
            user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        assert artifact_create_with_filename_test(
            user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        assert artifact_create_with_filename_test(user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED)

    def test_artifact_create_with_multipart_one_part(self):
        """
        Test if create artifact with multipart work and confirm it only work for project admins and members
        """

        def artifact_create_with_multipart_one_part_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.artifact_url,
                {
                    "run_suuid": self.runs["run_1"].suuid,
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("project").get("suuid") == self.runs["run_1"].jobdef.project.suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == "application/zip"

            artifact_suuid = response.data.get("suuid")
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
            assert response.data.get("created_for").get("suuid") == artifact_suuid

            File.objects.get(suuid=response.data.get("suuid")).delete_file_and_empty_directories()

            return True

        assert (
            artifact_create_with_multipart_one_part_test(
                user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )
        assert (
            artifact_create_with_multipart_one_part_test(
                user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )

        assert (
            artifact_create_with_multipart_one_part_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_multipart_one_part_test(
                user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_multipart_one_part_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_create_with_multipart_one_part_test(
                user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED
            )
            is True
        )

    def test_artifact_create_with_multipart_multiple_parts(self):
        """
        Test if create artifact with multipart work and confirm it only work for project admins and members
        """

        def artifact_createwith_multipart_multiple_parts_test(
            user_name: str | None, expected_status_code: int
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.artifact_url,
                {
                    "run_suuid": self.runs["run_1"].suuid,
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expected_status_code != status.HTTP_201_CREATED:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == 201
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("project").get("suuid") == self.runs["run_1"].jobdef.project.suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == "application/zip"

            artifact_suuid = response.data.get("suuid")
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
            assert response.data.get("created_for").get("suuid") == artifact_suuid

            File.objects.get(suuid=response.data.get("suuid")).delete_file_and_empty_directories()

            return True

        assert (
            artifact_createwith_multipart_multiple_parts_test(
                user_name="workspace_admin", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )
        assert (
            artifact_createwith_multipart_multiple_parts_test(
                user_name="workspace_member", expected_status_code=status.HTTP_201_CREATED
            )
            is True
        )

        assert (
            artifact_createwith_multipart_multiple_parts_test(
                user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_createwith_multipart_multiple_parts_test(
                user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_createwith_multipart_multiple_parts_test(
                user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND
            )
            is True
        )
        assert (
            artifact_createwith_multipart_multiple_parts_test(
                user_name=None, expected_status_code=status.HTTP_401_UNAUTHORIZED
            )
            is True
        )

    def test_create_artifact_without_run_suuid(self):
        artifact_url = reverse("run-artifact-list", kwargs={"version": "v1"})

        self.set_authorization("workspace_admin")
        response = self.client.post(artifact_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field is required." in response.data["run_suuid"]

    def test_create_artifact_with_not_existing_run_suuid(self):
        self.set_authorization("workspace_admin")

        response = self.client.post(
            self.artifact_url,
            {
                "run_suuid": "1234-1234-1234-1234",
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_artifact_without_filename_or_artifact(self):
        self.set_authorization("workspace_admin")

        response = self.client.post(
            self.artifact_url,
            {
                "run_suuid": self.runs["run_1"].suuid,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("detail") == "artifact or filename is required"

    def test_artifact_create_with_file_and_wrong_etag(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as artifact:
            response = self.client.post(
                self.artifact_url,
                {
                    "run_suuid": self.runs["run_1"].suuid,
                    "artifact": artifact,
                    "etag": 1,
                    "size": self.zipfile["size"],
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"ETag '1' does not match the ETag of the received file '{self.zipfile['etag']}'." in response.data.get(
            "etag"
        )

    def test_artifact_create_with_file_and_wrong_size(self):
        self.set_authorization(self.users["workspace_admin"])

        with self.zipfile["file"].open("rb") as artifact:
            response = self.client.post(
                self.artifact_url,
                {
                    "run_suuid": self.runs["run_1"].suuid,
                    "artifact": artifact,
                    "size": 1,
                },
                format="multipart",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"Size '1' does not match the size of the received file '{self.zipfile['size']}'." in response.data.get(
            "size"
        )

    def test_artifact_create_with_file_and_wrong_content_type(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.post(
            self.artifact_url,
            {
                "run_suuid": self.runs["run_1"].suuid,
                "artifact": self.avatar_file,
                "size": 1,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only zip files are allowed for artifacts" in response.data.get("artifact")
