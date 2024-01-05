from django.urls import reverse
from rest_framework import status

from job.tests.base import BaseAPITestJob


class TestJobListAPI(BaseAPITestJob):
    """
    Test to list the JobDefs
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        """
        We cann list job as an AskAnna admin but only for public projects
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_viewer(self):
        """
        We can list job as member of a workspace
        """
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_non_member(self):
        """
        We can list job as non-member of a workspace but only for public projects
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_anonymous(self):
        """
        Anonymous user can only list public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


class TestJobListWithProjectFilterAPI(BaseAPITestJob):
    """
    Test to list the JobDefs in a project
    """

    def setUp(self):
        super().setUp()
        self.url = (
            reverse("job-list", kwargs={"version": "v1"}) + "?project_suuid=" + self.projects["project_private"].suuid
        )

    def test_list_as_askanna_admin(self):
        """
        We cann list job as an AskAnna admin but only for public projects
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_non_member(self):
        """
        We can list job as non-member of a workspace but only for public projects
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_anonymous(self):
        """
        We can list job as anonymous but only for public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


class TestJobDetailAPI(BaseAPITestJob):
    """
    Test to get details of a JobDef
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={
                "version": "v1",
                "suuid": self.jobs["job_private"].suuid,
            },
        )

    def test_detail_as_askanna_admin(self):
        """
        We cannot get details of a jobdef from a private workspace as an AskAnna admin
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_admin(self):
        """
        We can get details of a jobdef as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobs["job_private"].suuid

    def test_detail_as_member(self):
        """
        We can get details of a jobdef as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobs["job_private"].suuid

    def test_detail_as_non_member(self):
        """
        We cannot get details of a jobdef from a private workspace as non member
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_anonymous(self):
        """
        We cannot get details of a jobdef from a private workspace as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobChangeAPI(BaseAPITestJob):
    """
    Test to change a Jobdef
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={
                "version": "v1",
                "suuid": self.jobs["job_private"].suuid,
            },
        )

    def test_change_as_askanna_admin(self):
        """
        We cannot change a jobdef as an AskAnna admin
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_change_as_admin(self):
        """
        We can change a jobdef as an admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobs["job_private"].suuid
        assert response.data["name"] == "newname"
        assert response.data["description"] == "test"

    def test_change_as_member(self):
        """
        We can change a jobdef as a member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobs["job_private"].suuid
        assert response.data["name"] == "newname"
        assert response.data["description"] == "test"

    def test_change_as_non_member(self):
        """
        We cannot change a jobdef as non-member
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_change_as_anonymous(self):
        """
        We cannot change a jobdef as anonymous
        """
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobDeleteAPI(BaseAPITestJob):
    """
    Test to delete a JobDef
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={
                "version": "v1",
                "suuid": self.jobs["job_private"].suuid,
            },
        )

    def test_delete_as_anna(self):
        """
        By default, AskAnna user cannot delete jobs (not a member)
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_admin(self):
        """
        Delete a job as a workspace admin
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_member(self):
        """
        Delete a job as a workspace member
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_nonmember(self):
        """
        Non workspace members cannot delete jobs
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_anonymous(self):
        """
        Anonymous users cannot delete jobs
        """

        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
