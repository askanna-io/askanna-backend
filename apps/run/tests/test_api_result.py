import pytest
from django.urls import reverse
from rest_framework import status

from core.tests.base import BaseUploadTestMixin
from run.tests.base import BaseAPITestRun


class TestRunResultAPI(BaseAPITestRun):
    """
    Test to get result of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-result",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_2"].suuid,
            },
        )

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot get the result for a run as an AskAnna admin
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_admin(self):
        """
        We can get the result for a run as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_as_member(self):
        """
        We can get the result for a run as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_as_non_member(self):
        """
        We cannot get the result for a run as a non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the result of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResultDetailAPI(BaseAPITestRun):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-result",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_2"].suuid,
            },
        )

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot retrieve the result as an AskAnna admin while not being a member of the workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_admin(self):
        """
        We can retrieve the result as an admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"some result content"

    def test_retrieve_as_member(self):
        """
        We can retrieve the result as a member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"some result content"

    def test_retrieve_as_viewer(self):
        """
        We can retrieve the result as a viewer of a workspace
        """
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"some result content"

    def test_retrieve_as_non_member(self):
        """
        We cannot retrieve the result when not being a member of the workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the result as anonymous user
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResultCreateUploadAPI(BaseUploadTestMixin, BaseAPITestRun):
    """
    Test on creating result and uploading chunks
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
        self.register_upload_url = reverse(
            "run-result-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run_1"].suuid,
            },
        )
        self.create_chunk_url = lambda result_object: reverse(
            "result-resultchunk-list",
            kwargs={
                "version": "v1",
                "parent_lookup_runresult__run__suuid": self.runs["run_1"].suuid,
                "parent_lookup_runresult__suuid": result_object.get("suuid"),
            },
        )
        self.upload_chunk_url = lambda result_object, chunk_suuid: reverse(
            "result-resultchunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_runresult__run__suuid": self.runs["run_1"].suuid,
                "parent_lookup_runresult__suuid": result_object.get("suuid"),
                "suuid": chunk_suuid,
            },
        )
        self.finish_upload_url = lambda result_object: reverse(
            "run-result-finish-upload",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run_1"].suuid,
                "suuid": result_object.get("suuid"),
            },
        )

    def check_retrieve_output(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        # also try the range request
        response = self.client.get(self.url, HTTP_RANGE="bytes=5-10")
        assert response.status_code == status.HTTP_206_PARTIAL_CONTENT

        # also try the range request for full file (larger than the file itself)
        response = self.client.get(self.url, HTTP_RANGE="bytes=0-100000")
        assert response.status_code == status.HTTP_206_PARTIAL_CONTENT

    def run_test(self, user=None):
        if user:
            self.set_authorization(self.users[user])

        self.do_file_upload(
            create_url=self.register_upload_url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-result-admin.zip",
        )

        self.check_retrieve_output()

        return True

    def test_create_as_askanna_admin(self):
        """
        AskAnna admins cannot create results
        """
        with pytest.raises(AssertionError):
            self.run_test(user="askanna_super_admin")

    def test_create_as_admin(self):
        """
        We can create result as admin of a workspace
        """
        assert self.run_test(user="workspace_admin") is True

    def test_create_as_member(self):
        """
        We can create result as member of a workspace
        """
        assert self.run_test(user="workspace_member") is True

    def test_create_as_viewer(self):
        """
        Workspace viewers cannot create result (cannot start run)
        """
        with pytest.raises(AssertionError):
            self.run_test(user="workspace_viewer")

    def test_create_as_non_member(self):
        """
        Non-members cannot create results
        """
        with pytest.raises(AssertionError):
            self.run_test(user="no_workspace_member")

    def test_create_as_anonymous(self):
        """
        Anonymous cannot create results
        """
        with pytest.raises(AssertionError):
            self.run_test(user=None)
