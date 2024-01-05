import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun
from storage.models import File
from storage.utils.file import get_md5_from_file


class TestRunResultAPI(BaseAPITestRun):
    def _test_get_result(
        self, user_name: str | None = None, run: str = "run_1", expected_status_code=status.HTTP_200_OK
    ):
        self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()
        run_url = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs[run].suuid,
            },
        )

        download_url = reverse(
            "storage-file-download",
            kwargs={
                "version": "v1",
                "suuid": self.runs[run].result.suuid,
            },
        )

        response = self.client.get(run_url)
        assert response.status_code == expected_status_code
        if expected_status_code == status.HTTP_200_OK:
            assert isinstance(response.data["result"], dict)

            result = response.data["result"]
            assert result["filename"] == self.runs[run].result.name

            assert download_url in result["download_info"]["url"]

        response = self.client.get(download_url)
        expected_status_code = (
            status.HTTP_401_UNAUTHORIZED
            if user_name is None and expected_status_code != status.HTTP_200_OK
            else expected_status_code
        )
        assert response.status_code == expected_status_code
        if expected_status_code == status.HTTP_200_OK:
            assert response["Content-Disposition"] == f'attachment; filename="{self.runs[run].result.name}"'
            assert b"".join(response.streaming_content) == self.runs[run].result.file.read()

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot retrieve the result as an AskAnna admin while not being a member of the workspace
        """
        self._test_get_result(
            user_name="askanna_super_admin", run="run_2", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        self._test_get_result(user_name="askanna_super_admin", run="run_4")

    def test_retrieve_as_admin(self):
        """
        We can retrieve the result as an admin of a workspace
        """
        self._test_get_result(user_name="workspace_admin", run="run_2")
        self._test_get_result(user_name="workspace_admin", run="run_4")

    def test_retrieve_as_member(self):
        """
        We can retrieve the result as a member of a workspace
        """
        self._test_get_result(user_name="workspace_member", run="run_2")
        self._test_get_result(user_name="workspace_member", run="run_4")

    def test_retrieve_as_viewer(self):
        """
        We can retrieve the result as a viewer of a workspace
        """
        self._test_get_result(user_name="workspace_viewer", run="run_2")
        self._test_get_result(user_name="workspace_viewer", run="run_4")

    def test_retrieve_as_non_member(self):
        """
        We cannot retrieve the result when not being a member of the workspace
        """
        self._test_get_result(
            user_name="no_workspace_member", run="run_2", expected_status_code=status.HTTP_404_NOT_FOUND
        )
        self._test_get_result(user_name="no_workspace_member", run="run_4")

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the result as anonymous user
        """
        self._test_get_result(run="run_2", expected_status_code=status.HTTP_404_NOT_FOUND)
        self._test_get_result(run="run_4")


class TestResultCreateUploadAPI(BaseAPITestRun):
    """
    Test on creating result and uploading parts
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-result",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_1"].suuid,
            },
        )

    @pytest.fixture(autouse=True)
    def _set_result_fixtures(self, mixed_format_zipfile):
        self.zipfile = mixed_format_zipfile

    def test_result_create_with_file(self):
        """
        Test if create result with file work and confirm it only work for project admins and members
        """

        def result_create_with_file_test(user_name: str | None, expect_to_fail: bool = False) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as result:
                response = self.client.post(
                    self.url,
                    {
                        "result": result,
                    },
                    format="multipart",
                )

            if expect_to_fail is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"
            assert response.data.get("download_info").get("url") is not None
            assert response.data.get("upload_info") is None

            # Clean up
            self.runs["run_1"].refresh_from_db()
            result_file_suuid = self.runs["run_1"].result.suuid
            self.runs["run_1"].result = None
            self.runs["run_1"].save()
            File.objects.get(suuid=result_file_suuid).delete()

            return True

        assert result_create_with_file_test(user_name="workspace_admin") is True
        assert result_create_with_file_test(user_name="workspace_member") is True

        assert result_create_with_file_test(user_name="askanna_super_admin", expect_to_fail=True) is True
        assert result_create_with_file_test(user_name="workspace_viewer", expect_to_fail=True) is True
        assert result_create_with_file_test(user_name="no_workspace_member", expect_to_fail=True) is True
        assert result_create_with_file_test(user_name=None, expect_to_fail=True) is True

    def test_result_create_with_file_and_meta_info(self):
        """
        Test if create result with file and meta info work and confirm it only work for project admins and members
        """

        def result_create_with_file_and_meta_info_test(user_name: str | None, expect_to_fail: bool = False) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as result:
                response = self.client.post(
                    self.url,
                    {
                        "result": result,
                        "etag": self.zipfile["etag"],
                        "size": self.zipfile["size"],
                        "content_type": self.zipfile["content_type"],
                    },
                    format="multipart",
                )

            if expect_to_fail is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") == self.zipfile["size"]
            assert response.data.get("etag") == self.zipfile["etag"]
            assert response.data.get("content_type") == "application/zip"
            assert response.data.get("download_info").get("url") is not None
            assert response.data.get("upload_info") is None

            # Clean up
            self.runs["run_1"].refresh_from_db()
            result_file_suuid = self.runs["run_1"].result.suuid
            self.runs["run_1"].result = None
            self.runs["run_1"].save()
            File.objects.get(suuid=result_file_suuid).delete()

            return True

        assert result_create_with_file_and_meta_info_test(user_name="workspace_admin") is True
        assert result_create_with_file_and_meta_info_test(user_name="workspace_member") is True

        assert result_create_with_file_and_meta_info_test(user_name="askanna_super_admin", expect_to_fail=True) is True
        assert result_create_with_file_and_meta_info_test(user_name="workspace_viewer", expect_to_fail=True) is True
        assert result_create_with_file_and_meta_info_test(user_name="no_workspace_member", expect_to_fail=True) is True
        assert result_create_with_file_and_meta_info_test(user_name=None, expect_to_fail=True) is True

    def test_result_create_with_filename(self):
        """
        Test if create result with filename work and confirm it only work for project admins and members
        """

        def result_create_with_filename_test(user_name: str | None, expect_to_fail: bool = False) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.url,
                {
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expect_to_fail is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == ""
            assert response.data.get("download_info") is None
            assert response.data.get("upload_info").get("url") is not None

            # Clean up
            self.runs["run_1"].refresh_from_db()
            result_file_suuid = self.runs["run_1"].result.suuid
            self.runs["run_1"].result = None
            self.runs["run_1"].save()
            File.objects.get(suuid=result_file_suuid).delete()

            return True

        assert result_create_with_filename_test(user_name="workspace_admin") is True
        assert result_create_with_filename_test(user_name="workspace_member") is True

        assert result_create_with_filename_test(user_name="askanna_super_admin", expect_to_fail=True) is True
        assert result_create_with_filename_test(user_name="workspace_viewer", expect_to_fail=True) is True
        assert result_create_with_filename_test(user_name="no_workspace_member", expect_to_fail=True) is True
        assert result_create_with_filename_test(user_name=None, expect_to_fail=True) is True

    def test_result_create_with_multipart_one_part(self):
        """
        Test if create result with multipart work and confirm it only work for project admins and members
        """

        def result_create_with_multipart_one_part_test(user_name: str | None, expect_to_fail: bool = False) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.url,
                {
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expect_to_fail is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == ""
            assert response.data.get("download_info") is None
            assert response.data.get("upload_info").get("url") is not None

            run_suuid = response.data.get("run").get("suuid")
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
            assert response.data.get("created_for").get("suuid") == run_suuid

            # Clean up
            self.runs["run_1"].refresh_from_db()
            result_file_suuid = self.runs["run_1"].result.suuid
            self.runs["run_1"].result = None
            self.runs["run_1"].save()
            File.objects.get(suuid=result_file_suuid).delete()

            return True

        assert result_create_with_multipart_one_part_test(user_name="workspace_admin") is True
        assert result_create_with_multipart_one_part_test(user_name="workspace_member") is True

        assert result_create_with_multipart_one_part_test(user_name="askanna_super_admin", expect_to_fail=True) is True
        assert result_create_with_multipart_one_part_test(user_name="workspace_viewer", expect_to_fail=True) is True
        assert result_create_with_multipart_one_part_test(user_name="no_workspace_member", expect_to_fail=True) is True
        assert result_create_with_multipart_one_part_test(user_name=None, expect_to_fail=True) is True

    def test_result_create_with_multipart_multiple_parts(self):
        """
        Test if create result with multipart and multiple parts work and confirm it only work for project admins
        and members
        """

        def result_create_with_multipart_multiple_parts_test(
            user_name: str | None, expect_to_fail: bool = False
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.url,
                {
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expect_to_fail is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data.get("run").get("suuid") == self.runs["run_1"].suuid
            assert response.data.get("filename") == "mixed_format_archive.zip"
            assert response.data.get("size") is None
            assert response.data.get("etag") == ""
            assert response.data.get("content_type") == ""
            assert response.data.get("download_info") is None
            assert response.data.get("upload_info").get("url") is not None

            run_suuid = response.data.get("run").get("suuid")
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
            assert response.data.get("created_for").get("suuid") == run_suuid

            # Clean up
            self.runs["run_1"].refresh_from_db()
            result_file_suuid = self.runs["run_1"].result.suuid
            self.runs["run_1"].result = None
            self.runs["run_1"].save()
            File.objects.get(suuid=result_file_suuid).delete()

            return True

        assert result_create_with_multipart_multiple_parts_test(user_name="workspace_admin") is True
        assert result_create_with_multipart_multiple_parts_test(user_name="workspace_member") is True

        assert (
            result_create_with_multipart_multiple_parts_test(user_name="askanna_super_admin", expect_to_fail=True)
            is True
        )
        assert (
            result_create_with_multipart_multiple_parts_test(user_name="workspace_viewer", expect_to_fail=True) is True
        )
        assert (
            result_create_with_multipart_multiple_parts_test(user_name="no_workspace_member", expect_to_fail=True)
            is True
        )
        assert result_create_with_multipart_multiple_parts_test(user_name=None, expect_to_fail=True) is True

    def test_result_create_with_not_existing_run_suuid(self):
        """
        Test if create result with invalid run suuid result in not found
        """

        def result_create_with_not_existing_run_suuid_test(user_name: str | None) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                reverse(
                    "run-result",
                    kwargs={
                        "version": "v1",
                        "suuid": "1234-1234-1234-1234",
                    },
                ),
                {
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            return True

        assert result_create_with_not_existing_run_suuid_test(user_name="workspace_admin") is True
        assert result_create_with_not_existing_run_suuid_test(user_name="workspace_member") is True

        assert result_create_with_not_existing_run_suuid_test(user_name="askanna_super_admin") is True
        assert result_create_with_not_existing_run_suuid_test(user_name="workspace_viewer") is True
        assert result_create_with_not_existing_run_suuid_test(user_name="no_workspace_member") is True
        assert result_create_with_not_existing_run_suuid_test(user_name=None) is True

    def test_result_create_with_already_existing_result(self):
        """
        Test if create result with filename work and confirm it only work for project admins and members
        """

        def result_create_with_already_existing_result_test(
            user_name: str | None, expect_bad_request: bool = False, expect_no_access: bool = False
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                reverse(
                    "run-result",
                    kwargs={
                        "version": "v1",
                        "suuid": self.runs["run_2"].suuid,
                    },
                ),
                {
                    "filename": "mixed_format_archive.zip",
                },
                format="multipart",
            )

            if expect_bad_request is True:
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert response.data.get("detail") == "Run already has a result"
                return True

            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            return False

        assert (
            result_create_with_already_existing_result_test(user_name="workspace_admin", expect_bad_request=True)
            is True
        )
        assert (
            result_create_with_already_existing_result_test(user_name="workspace_member", expect_bad_request=True)
            is True
        )

        assert (
            result_create_with_already_existing_result_test(user_name="askanna_super_admin", expect_no_access=True)
            is True
        )
        assert (
            result_create_with_already_existing_result_test(user_name="workspace_viewer", expect_no_access=True)
            is True
        )
        assert (
            result_create_with_already_existing_result_test(user_name="no_workspace_member", expect_no_access=True)
            is True
        )
        assert result_create_with_already_existing_result_test(user_name=None, expect_no_access=True) is True

    def test_result_create_without_filename_or_file(self):
        """
        Test if create result without filename or file result in bad request and confirm it only work for
        project admins and members
        """

        def result_create_without_filename_or_file_test(
            user_name: str | None, expect_bad_request: bool = False, expect_no_access: bool = False
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.post(
                self.url,
                format="multipart",
            )

            if expect_bad_request is True:
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert response.data.get("detail") == "result or filename is required"
                return True

            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            raise ValueError(
                "This test should not be able to reach this point. Set expect_bad_request or expect_no_access to True."
            )

        assert (
            result_create_without_filename_or_file_test(user_name="workspace_admin", expect_bad_request=True) is True
        )
        assert (
            result_create_without_filename_or_file_test(user_name="workspace_member", expect_bad_request=True) is True
        )

        assert (
            result_create_without_filename_or_file_test(user_name="askanna_super_admin", expect_no_access=True) is True
        )
        assert result_create_without_filename_or_file_test(user_name="workspace_viewer", expect_no_access=True) is True
        assert (
            result_create_without_filename_or_file_test(user_name="no_workspace_member", expect_no_access=True) is True
        )
        assert result_create_without_filename_or_file_test(user_name=None, expect_no_access=True) is True

    def test_result_create_with_file_and_wrong_etag(self):
        """
        Test if create result with file and wrong etag result in bad request and confirm it only work for
        project admins and members
        """

        def result_create_with_file_and_wrong_etag_test(
            user_name: str | None, expect_bad_request: bool = False, expect_no_access: bool = False
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as result:
                response = self.client.post(
                    self.url,
                    {
                        "result": result,
                        "etag": "wrong_etag",
                    },
                    format="multipart",
                )

            if expect_bad_request is True:
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert (
                    f"ETag 'wrong_etag' does not match the ETag of the received file '{self.zipfile['etag']}'."
                    in response.data.get("etag")
                )
                return True

            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            raise ValueError(
                "This test should not be able to reach this point. Set expect_bad_request or expect_no_access to True."
            )

        assert (
            result_create_with_file_and_wrong_etag_test(user_name="workspace_admin", expect_bad_request=True) is True
        )
        assert (
            result_create_with_file_and_wrong_etag_test(user_name="workspace_member", expect_bad_request=True) is True
        )

        assert (
            result_create_with_file_and_wrong_etag_test(user_name="askanna_super_admin", expect_no_access=True) is True
        )
        assert result_create_with_file_and_wrong_etag_test(user_name="workspace_viewer", expect_no_access=True) is True
        assert (
            result_create_with_file_and_wrong_etag_test(user_name="no_workspace_member", expect_no_access=True) is True
        )
        assert result_create_with_file_and_wrong_etag_test(user_name=None, expect_no_access=True) is True

    def test_result_create_with_file_and_wrong_size(self):
        """
        Test if create result with file and wrong size result in bad request and confirm it only work for
        project admins and members
        """

        def result_create_with_file_and_wrong_size_test(
            user_name: str | None, expect_bad_request: bool = False, expect_no_access: bool = False
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as result:
                response = self.client.post(
                    self.url,
                    {
                        "result": result,
                        "size": 1,
                    },
                    format="multipart",
                )

            if expect_bad_request is True:
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert (
                    f"Size '1' does not match the size of the received file '{self.zipfile['size']}'."
                    in response.data.get("size")
                )
                return True

            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            raise ValueError(
                "This test should not be able to reach this point. Set expect_bad_request or expect_no_access to True."
            )

        assert (
            result_create_with_file_and_wrong_size_test(user_name="workspace_admin", expect_bad_request=True) is True
        )
        assert (
            result_create_with_file_and_wrong_size_test(user_name="workspace_member", expect_bad_request=True) is True
        )

        assert (
            result_create_with_file_and_wrong_size_test(user_name="askanna_super_admin", expect_no_access=True) is True
        )
        assert result_create_with_file_and_wrong_size_test(user_name="workspace_viewer", expect_no_access=True) is True
        assert (
            result_create_with_file_and_wrong_size_test(user_name="no_workspace_member", expect_no_access=True) is True
        )
        assert result_create_with_file_and_wrong_size_test(user_name=None, expect_no_access=True) is True

    def test_result_create_with_file_and_wrong_content_type(self):
        """
        Test if create result with file and wrong content_type result in bad request and confirm it only work for
        project admins and members
        """

        def result_create_with_file_and_wrong_content_type_test(
            user_name: str | None, expect_bad_request: bool = False, expect_no_access: bool = False
        ) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            with self.zipfile["file"].open("rb") as result:
                response = self.client.post(
                    self.url,
                    {
                        "result": result,
                        "content_type": "image/png",
                    },
                    format="multipart",
                )

            if expect_bad_request is True:
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert (
                    "Content type 'image/png' does not match the content type of the received file "
                    f"'{self.zipfile['content_type']}'." in response.data.get("content_type")
                )
                return True

            if expect_no_access is True:
                assert response.status_code == status.HTTP_404_NOT_FOUND
                return True

            raise ValueError(
                "This test should not be able to reach this point. Set expect_bad_request or expect_no_access to True."
            )

        assert (
            result_create_with_file_and_wrong_content_type_test(user_name="workspace_admin", expect_bad_request=True)
            is True
        )
        assert (
            result_create_with_file_and_wrong_content_type_test(user_name="workspace_member", expect_bad_request=True)
            is True
        )

        assert (
            result_create_with_file_and_wrong_content_type_test(user_name="askanna_super_admin", expect_no_access=True)
            is True
        )
        assert (
            result_create_with_file_and_wrong_content_type_test(user_name="workspace_viewer", expect_no_access=True)
            is True
        )
        assert (
            result_create_with_file_and_wrong_content_type_test(user_name="no_workspace_member", expect_no_access=True)
            is True
        )
        assert result_create_with_file_and_wrong_content_type_test(user_name=None, expect_no_access=True) is True
