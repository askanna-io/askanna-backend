from django.urls import reverse
from rest_framework import status

from core.tests.base import BaseUploadTestMixin
from run.tests.base import BaseAPITestRun


class TestArtifactListAPI(BaseAPITestRun):
    """
    Test to list the artifacts
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-artifact-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run_1"].suuid,
            },
        )

    def test_list_as_askanna_admin(self):
        """
        We cannot list artifacts as an AskAnna admin who is not a member of the workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_admin(self):
        """
        We can list artifacts as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["suuid"] == self.artifacts["artifact_1"].suuid
        assert response.data["results"][0]["size"] == self.artifacts["artifact_1"].size

    def test_list_as_member(self):
        """
        We can list artifacts as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["suuid"] == self.artifacts["artifact_1"].suuid
        assert response.data["results"][0]["size"] == self.artifacts["artifact_1"].size

    def test_list_as_non_member(self):
        """
        We cannot list artifacts as non-member of a workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_anonymous(self):
        """
        We cannot list artifacts as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


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
                "parent_lookup_run__suuid": self.runs["run_1"].suuid,
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
        assert response.data["size"] == self.artifacts["artifact_1"].size

    def test_retrieve_as_member(self):
        """
        We can get artifacts as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.artifacts["artifact_1"].suuid
        assert response.data["size"] == self.artifacts["artifact_1"].size

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


class TestArtifactCreateUploadAPI(BaseUploadTestMixin, BaseAPITestRun):
    """
    Test on creating artifacts and uploading chunks
    """

    def setUp(self):
        super().setUp()
        self.register_upload_url = reverse(
            "run-artifact-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run_1"].suuid,
            },
        )
        self.create_chunk_url = lambda artifact_object: reverse(
            "artifact-artifactchunk-list",
            kwargs={
                "version": "v1",
                "parent_lookup_artifact__run__suuid": self.runs["run_1"].suuid,
                "parent_lookup_artifact__suuid": artifact_object.get("suuid"),
            },
        )
        self.upload_chunk_url = lambda artifact_object, chunk_suuid: reverse(
            "artifact-artifactchunk-chunk",
            kwargs={
                "version": "v1",
                "parent_lookup_artifact__run__suuid": self.runs["run_1"].suuid,
                "parent_lookup_artifact__suuid": artifact_object.get("suuid"),
                "suuid": chunk_suuid,
            },
        )
        self.finish_upload_url = lambda artifact_object: reverse(
            "run-artifact-finish-upload",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runs["run_1"].suuid,
                "suuid": artifact_object.get("suuid"),
            },
        )

    def run_test(self):
        self.do_file_upload(
            create_url=self.register_upload_url,
            create_chunk_url=self.create_chunk_url,
            upload_chunk_url=self.upload_chunk_url,
            finish_upload_url=self.finish_upload_url,
            fileobjectname="test-artifact-admin.zip",
        )

        return True

    def test_create_as_askanna_admin(self):
        """
        AskAnna admins cannot create artifacts in workspace they are not a member of
        """
        self.set_authorization(self.users["askanna_super_admin"])

        with self.assertRaises(AssertionError):
            assert self.run_test() is False

    def test_create_as_admin(self):
        """
        We can create artifacts as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        assert self.run_test() is True

    def test_create_as_member(self):
        """
        We can create artifacts as admin of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        assert self.run_test() is True

    def test_create_as_workspace_viewer(self):
        """
        Workspace viewers cannot create artifacts
        """
        self.set_authorization(self.users["workspace_viewer"])

        with self.assertRaises(AssertionError):
            assert self.run_test() is True

    def test_create_as_non_member(self):
        """
        Non-members cannot create artifacts
        """
        self.set_authorization(self.users["no_workspace_member"])

        with self.assertRaises(AssertionError):
            assert self.run_test() is False

    def test_create_as_anonymous(self):
        """
        Anonymous users cannot create artifacts
        """
        with self.assertRaises(AssertionError):
            assert self.run_test() is False
