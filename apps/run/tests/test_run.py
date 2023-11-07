from dateutil.parser import parse as date_parse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseRunTest
from tests.utils import get_avatar_content_file


class TestRunModel(BaseRunTest, APITestCase):
    """
    Test run model functions
    """

    def test_run_function__str__run_with_name(self):
        assert str(self.runs["run1"]) == f"run1 ({self.runs['run1'].suuid})"

    def test_run_function__str__run_with_no_name(self):
        assert str(self.runs["run7"]) == str(self.runs["run7"].suuid)

    def test_run_function_set_status(self):
        assert self.runs["run7"].status == "FAILED"
        modified_at_before = self.runs["run7"].modified_at

        self.runs["run7"].set_status("COMPLETED")
        assert self.runs["run7"].status == "COMPLETED"
        assert self.runs["run7"].modified_at > modified_at_before

        # Set status of run7 back to failed
        self.runs["run7"].set_status("FAILED")

    def test_run_function_set_finished_at(self):
        assert self.runs["run6"].finished_at is None
        assert self.runs["run6"].duration is None
        modified_at_before = self.runs["run6"].modified_at

        self.runs["run6"].set_finished_at()
        assert self.runs["run6"].modified_at > modified_at_before
        assert self.runs["run6"].finished_at is not None
        assert self.runs["run6"].finished_at > self.runs["run6"].started_at
        duration = (self.runs["run6"].finished_at - self.runs["run6"].started_at).seconds
        assert self.runs["run6"].duration == duration


class TestRunListAPI(BaseRunTest, APITestCase):
    """
    Test to list the runs
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-list",
            kwargs={"version": "v1"},
        )

    def test_list_as_askanna_admin(self):
        """
        We can list runs as an AskAnna admion but only for public projects
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "run6"

    def test_list_as_admin(self):
        """
        We can list runs as admin of a workspace
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 7

    def test_list_as_member(self):
        """
        We can list runs as member of a workspace
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_list_as_non_member(self):
        """
        We can list runs as non-member but only for public projects
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "run6"

    def test_list_as_anonymous(self):
        """
        We can list runs as anonymous but only for public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "run6"

    def test_list_as_member_filter_by_run(self):
        """
        We can list runs as member and filter by run
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"run_suuid": self.runs["run1"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_runs(self):
        """
        We can list runs as member and filter by multiple runs
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "run_suuid": ",".join(
                    [
                        self.runs["run1"].suuid,
                        self.runs["run2"].suuid,
                    ]
                )
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member_exclude_by_run(self):
        """
        We can list runs as member and exclude by run
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"run_suuid__exclude": self.runs["run1"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_filter_by_job(self):
        """
        We can list runs as member and filter by job
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"job_suuid": self.jobdef.suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_filter_by_jobs(self):
        """
        We can list runs as member and filter by multiple jobs
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "job_suuid": ",".join(
                    [
                        self.jobdef.suuid,
                        self.jobdef2.suuid,
                    ]
                )
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_exclude_by_job(self):
        """
        We can list runs as member and exclude by job
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"job_suuid__exclude": self.jobdef.suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_project(self):
        """
        We can list runs as member and filter by project
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.jobdef.project.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_exclude_by_project(self):
        """
        We can list runs as member and exclude by project
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "project_suuid__exclude": self.jobdef.project.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_workspace(self):
        """
        We can list runs as member and filter by workspace
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "workspace_suuid": self.jobdef.project.workspace.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_exclude_by_workspace(self):
        """
        We can list runs as member and exclude by workspace
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "workspace_suuid__exclude": self.jobdef.project.workspace.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_status(self):
        """
        We can list runs as member and filter by status
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "status": "finished",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member_filter_by_multiple_statuses(self):
        """
        We can list runs as member and filter by multiple statuses
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "status": "finished,failed",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_member_exclude_by_status(self):
        """
        We can list runs as member and exclude by status
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "status__exclude": "finished",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_member_filter_by_trigger(self):
        """
        We can list runs as member and filter by trigger
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "trigger": "webui",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_multiple_triggers(self):
        """
        We can list runs as member and filter by multiple triggers
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "trigger": "webui,cli",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member_exclude_by_trigger(self):
        """
        We can list runs as member and exclude by trigger
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "trigger__exclude": "webui",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_filter_by_created_by(self):
        """
        We can list runs as member and filter by created by
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "created_by_suuid": self.members.get("member").suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_exclude_by_created_by(self):
        """
        We can list runs as member and exclude by created by
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "created_by_suuid__exclude": self.members.get("member").suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_package_suuid(self):
        """
        We can list runs as member and filter by package suuid
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "package_suuid": self.package.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_list_as_member_exclude_by_package_suuid(self):
        """
        We can list runs as member and exclude by package suuid
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "package_suuid__exclude": self.package.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


class TestRunDetailAPI(BaseRunTest, APITestCase):
    """
    Test to get details of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-detail",
            kwargs={"version": "v1", "suuid": self.runs["run1"].suuid},
        )
        self.url_run2 = reverse(
            "run-detail",
            kwargs={"version": "v1", "suuid": self.runs["run2"].suuid},
        )
        self.url_other_workspace = reverse(
            "run-detail",
            kwargs={"version": "v1", "suuid": self.runs["run3"].suuid},
        )

    def test_detail_as_askanna_admin(self):
        """
        We cannot get details of a run as an AskAnna admin
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_admin(self):
        """
        We can get details of a run as an admin
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run1"].suuid

    def test_detail_as_member(self):
        """
        We can get details of a run as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run1"].suuid

    def test_detail_as_member_other_run(self):
        """
        We can get details of a run as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url_run2)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run2"].suuid
        assert response.data["result"]["name"] == "someresult.txt"
        assert response.data["result"]["extension"] == "txt"

    def test_detail_as_member_changed_membername(self):
        """
        We can get details of a run as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run1"].suuid
        assert response.data["created_by"]["name"] == "name of member in membership"

        # now change membername to new membername
        self.members.get("member").name = "new membername"
        self.members.get("member").save()

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run1"].suuid
        assert response.data["created_by"]["name"] == "new membername"

        # now change back new membername to membername
        self.members.get("member").name = "membername"
        self.members.get("member").save()

    def test_detail_as_member_workspace_membername_different_in_other_workspace(self):
        """
        We can get details of a run as a member
        """
        self.activate_user("member2")

        # Set avatar file for user
        self.members.get("member").set_avatar(get_avatar_content_file())

        # first visit 1st workspace
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run1"].suuid
        assert response.data["created_by"]["name"] == "name of member in membership"
        assert response.data["created_by"]["avatar_file"] is not None

        # then visit 2nd workspace
        response = self.client.get(self.url_other_workspace)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run3"].suuid
        assert response.data["created_by"]["name"] == "member2"

        # Delete avatar file for user
        self.members.get("member").delete_avatar_file()

    def test_detail_as_non_member(self):
        """
        We cannot get details of a run as non-member
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_anonymous(self):
        """
        We cannot get details of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunResultAPI(BaseRunTest, APITestCase):
    """
    Test to get result of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-result",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run2"].suuid,
            },
        )

    def test_retrieve_as_askanna_admin(self):
        """
        We cannot get the result for a run as an AskAnna admin
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_admin(self):
        """
        We can get the result for a run as an admin
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_as_member(self):
        """
        We can get the result for a run as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_as_non_member(self):
        """
        We cannot get the result for a run as a non-member
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_as_anonymous(self):
        """
        We cannot get the result of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunChangeAPI(BaseRunTest, APITestCase):
    """
    Test whether we can change the name and description of the run object
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run1"].suuid,
            },
        )
        self.url_run2 = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run2"].suuid,
            },
        )
        self.url_other_workspace = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run3"].suuid,
            },
        )

    def run_test(self):
        initial_response = self.client.get(self.url)
        assert initial_response.status_code == status.HTTP_200_OK
        assert initial_response.data["suuid"] == self.runs["run1"].suuid
        assert initial_response.data["name"] == self.runs["run1"].name
        assert initial_response.data["description"] == self.runs["run1"].description
        assert date_parse(initial_response.data["modified_at"]) == self.runs["run1"].modified_at

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run1"].suuid
        assert response.data["name"] == "new name"
        assert response.data["description"] == "new description"
        assert date_parse(response.data["modified_at"]) != self.runs["run1"].modified_at

        return True

    def test_update_as_askanna_admin(self):
        """
        We cannot update name and detail of the run as an AskAnna admin
        """
        self.activate_user("anna")

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_admin(self):
        """
        We can update name and detail of the run as admin
        """
        self.activate_user("admin")
        assert self.run_test() is True

    def test_update_as_member(self):
        """
        We can update name and detail of the run as member
        """
        self.activate_user("member")
        assert self.run_test() is True

    def test_update_as_non_member(self):
        """
        We cannot update name and detail of the run as non-member
        """
        self.activate_user("non_member")

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_anonymous(self):
        """
        We cannot update name and detail of the run as anonymous
        """
        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunDeleteAPI(BaseRunTest, APITestCase):
    """
    Test on the deletion of a Run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run1"].suuid,
            },
        )

    def run_test(self):
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        return True

    def test_delete_as_anna(self):
        """
        AskAnna admin by default don't have the permission to delete a run
        """
        self.activate_user("anna")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_admin(self):
        """
        We can remove a run as an workspace admin
        """
        self.activate_user("admin")
        assert self.run_test() is True

    def test_delete_as_member(self):
        """
        We can remove a run as a member of an workspace
        """
        self.activate_user("member")
        assert self.run_test() is True

    def test_delete_as_non_member(self):
        """
        We cannot remove a run when we are not a member of the workspace
        """
        self.activate_user("non_member")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_anonymous(self):
        """
        As anonoymous user we cannot remove a run
        """
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
