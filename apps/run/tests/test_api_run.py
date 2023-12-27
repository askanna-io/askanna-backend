from dateutil.parser import parse as date_parse
from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestRunListAPI(BaseAPITestRun):
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
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "test run 4 public"

    def test_list_as_admin(self):
        """
        We can list runs as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_list_as_member(self):
        """
        We can list runs as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_list_as_non_member(self):
        """
        We can list runs as non-member but only for public projects
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "test run 4 public"

    def test_list_as_anonymous(self):
        """
        We can list runs as anonymous but only for public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "test run 4 public"

    def test_list_as_member_filter_by_run(self):
        """
        We can list runs as member and filter by run
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"run_suuid": self.runs["run_1"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_runs(self):
        """
        We can list runs as member and filter by multiple runs
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "run_suuid": ",".join(
                    [
                        self.runs["run_1"].suuid,
                        self.runs["run_2"].suuid,
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
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"run_suuid__exclude": self.runs["run_1"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_filter_by_job(self):
        """
        We can list runs as member and filter by job
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"job_suuid": self.jobs["my-test-job"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member_filter_by_jobs(self):
        """
        We can list runs as member and filter by multiple jobs
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "job_suuid": ",".join(
                    [
                        self.jobs["my-test-job"].suuid,
                        self.jobs["job_private"].suuid,
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
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"job_suuid__exclude": self.jobs["my-test-job"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_member_filter_by_project(self):
        """
        We can list runs as member and filter by project
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.jobs["my-test-job"].project.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_exclude_by_project(self):
        """
        We can list runs as member and exclude by project
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "project_suuid__exclude": self.jobs["my-test-job"].project.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_workspace(self):
        """
        We can list runs as member and filter by workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "workspace_suuid": self.jobs["my-test-job"].project.workspace.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_exclude_by_workspace(self):
        """
        We can list runs as member and exclude by workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "workspace_suuid__exclude": self.jobs["my-test-job"].project.workspace.suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_status(self):
        """
        We can list runs as member and filter by status
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "status": "finished",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_filter_by_multiple_statuses(self):
        """
        We can list runs as member and filter by multiple statuses
        """
        self.set_authorization(self.users["workspace_member"])

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
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "status__exclude": "finished",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_filter_by_trigger(self):
        """
        We can list runs as member and filter by trigger
        """
        self.set_authorization(self.users["workspace_member"])

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
        self.set_authorization(self.users["workspace_member"])

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
        self.set_authorization(self.users["workspace_member"])

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
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "created_by_suuid": self.memberships["workspace_private_member"].suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_exclude_by_created_by(self):
        """
        We can list runs as member and exclude by created by
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "created_by_suuid__exclude": self.memberships["workspace_private_member"].suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member_filter_by_package_suuid(self):
        """
        We can list runs as member and filter by package suuid
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "package_suuid": self.packages["package_public"].suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member_exclude_by_package_suuid(self):
        """
        We can list runs as member and exclude by package suuid
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "package_suuid__exclude": self.packages["package_public"].suuid,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4


class TestRunDetailAPI(BaseAPITestRun):
    """
    Test to get details of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_1"].suuid,
            },
        )

    def test_detail_as_askanna_admin(self):
        """
        We cannot get details of a run as an AskAnna admin
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_admin(self):
        """
        We can get details of a run as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run_1"].suuid

    def test_detail_as_member(self):
        """
        We can get details of a run as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run_1"].suuid

    def test_detail_as_non_member(self):
        """
        We cannot get details of a run as non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_anonymous(self):
        """
        We cannot get details of a run as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunChangeAPI(BaseAPITestRun):
    """
    Test whether we can change the name and description of the run object
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_1"].suuid,
            },
        )

    def run_test(self):
        initial_response = self.client.get(self.url)
        assert initial_response.status_code == status.HTTP_200_OK
        assert initial_response.data["suuid"] == self.runs["run_1"].suuid
        assert initial_response.data["name"] == self.runs["run_1"].name
        assert initial_response.data["description"] == self.runs["run_1"].description
        assert date_parse(initial_response.data["modified_at"]) == self.runs["run_1"].modified_at

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.runs["run_1"].suuid
        assert response.data["name"] == "new name"
        assert response.data["description"] == "new description"
        assert date_parse(response.data["modified_at"]) != self.runs["run_1"].modified_at

        return True

    def test_update_as_askanna_admin(self):
        """
        We cannot update name and detail of the run as an AskAnna admin
        """
        self.set_authorization(self.users["askanna_super_admin"])

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
        self.set_authorization(self.users["workspace_admin"])
        assert self.run_test() is True

    def test_update_as_member(self):
        """
        We can update name and detail of the run as member
        """
        self.set_authorization(self.users["workspace_member"])
        assert self.run_test() is True

    def test_update_as_non_member(self):
        """
        We cannot update name and detail of the run as non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

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


class TestRunDeleteAPI(BaseAPITestRun):
    """
    Test on the deletion of a Run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-detail",
            kwargs={
                "version": "v1",
                "suuid": self.runs["run_1"].suuid,
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
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_admin(self):
        """
        We can remove a run as an workspace admin
        """
        self.set_authorization(self.users["workspace_admin"])

        assert self.run_test() is True

    def test_delete_as_member(self):
        """
        We can remove a run as a member of an workspace
        """
        self.set_authorization(self.users["workspace_member"])

        assert self.run_test() is True

    def test_delete_as_non_member(self):
        """
        We cannot remove a run when we are not a member of the workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_anonymous(self):
        """
        As anonoymous user we cannot remove a run
        """
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
