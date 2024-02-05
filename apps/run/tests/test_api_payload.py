from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestRunPayloadAPI(BaseAPITestRun):
    """
    Test get the payload of a run
    """

    def _test_get_payload(self, user_name: str | None = None, run: str = "run_1", expect_no_access: bool = False):
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
                "suuid": self.runs[run].payload_file.suuid,
            },
        )

        response = self.client.get(run_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND if expect_no_access else status.HTTP_200_OK

        if expect_no_access is False:
            assert isinstance(response.data["payload"], dict)

            payload = response.data["payload"]
            assert payload["filename"] == self.runs[run].payload_file.name

            assert download_url in payload["download_info"]["url"]

        response = self.client.get(download_url)

        if expect_no_access is False:
            assert response.status_code == status.HTTP_200_OK
            assert response["Content-Disposition"] == f'attachment; filename="{self.runs[run].payload_file.name}"'
            assert response["Content-Type"] == "application/json"
            assert b"".join(response.streaming_content) == self.runs[run].payload_file.file.read()
        else:
            assert (
                response.status_code == status.HTTP_401_UNAUTHORIZED
                if user_name is None
                else status.HTTP_404_NOT_FOUND
            )

        return True

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot retrieve the result as an AskAnna admin while not being a member of the workspace
        """
        self._test_get_payload(user_name="askanna_super_admin", run="run_2", expect_no_access=True)
        self._test_get_payload(user_name="askanna_super_admin", run="run_4")

    def test_retrieve_as_admin(self):
        """
        We can retrieve the result as an admin of a workspace
        """
        self._test_get_payload(user_name="workspace_admin", run="run_2")
        self._test_get_payload(user_name="workspace_admin", run="run_4")

    def test_retrieve_as_member(self):
        """
        We can retrieve the result as a member of a workspace
        """
        self._test_get_payload(user_name="workspace_member", run="run_2")
        self._test_get_payload(user_name="workspace_member", run="run_4")

    def test_retrieve_as_viewer(self):
        """
        We can retrieve the result as a viewer of a workspace
        """
        self._test_get_payload(user_name="workspace_viewer", run="run_2")
        self._test_get_payload(user_name="workspace_viewer", run="run_4")

    def test_retrieve_as_non_member(self):
        """
        We cannot retrieve the result when not being a member of the workspace
        """
        self._test_get_payload(user_name="no_workspace_member", run="run_2", expect_no_access=True)
        self._test_get_payload(user_name="no_workspace_member", run="run_4")

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the result as anonymous user
        """
        self._test_get_payload(run="run_2", expect_no_access=True)
        self._test_get_payload(run="run_4")
