import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef

pytestmark = pytest.mark.django_db


class TestJobListAPI(BaseJobTestDef, APITestCase):
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
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 6  # type: ignore

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_non_member(self):
        """
        We can list job as non-member of a workspace but only for public projects
        """
        self.activate_user("non_member")

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_anonymous(self):
        """
        Anonymous user can only list public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore


class TestJobListWithProjectFilterAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the JobDefs in a project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("job-list", kwargs={"version": "v1"}) + "?project_suuid=" + self.project.suuid

    def test_list_as_askanna_admin(self):
        """
        We cann list job as an AskAnna admin but only for public projects
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_non_member(self):
        """
        We can list job as non-member of a workspace but only for public projects
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        print(response.data)
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_anonymous(self):
        """
        We can list job as anonymous but only for public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore


class TestJobDetailAPI(BaseJobTestDef, APITestCase):
    """
    Test to get details of a JobDef
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={
                "version": "v1",
                "suuid": self.jobdef.suuid,
            },
        )

    def test_detail_as_askanna_admin(self):
        """
        We cannot get details of a jobdef from a private workspace as an AskAnna admin
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_admin(self):
        """
        We can get details of a jobdef as an admin
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobdef.suuid  # type: ignore

    def test_detail_as_member(self):
        """
        We can get details of a jobdef as a member
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobdef.suuid  # type: ignore

    def test_detail_as_non_member(self):
        """
        We cannot get details of a jobdef from a private workspace as non member
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_anonymous(self):
        """
        We cannot get details of a jobdef from a private workspace as anonymous
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobChangeAPI(BaseJobTestDef, APITestCase):
    """
    Test to change a Jobdef
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={
                "version": "v1",
                "suuid": self.jobdef.suuid,
            },
        )

    def test_change_as_askanna_admin(self):
        """
        We cannot change a jobdef as an AskAnna admin
        """
        self.activate_user("anna")
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
        self.activate_user("admin")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobdef.suuid  # type: ignore
        assert response.data["name"] == "newname"  # type: ignore
        assert response.data["description"] == "test"  # type: ignore

    def test_change_as_member(self):
        """
        We can change a jobdef as a member
        """
        self.activate_user("member")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "description": "test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobdef.suuid  # type: ignore
        assert response.data["name"] == "newname"  # type: ignore
        assert response.data["description"] == "test"  # type: ignore

    def test_change_as_non_member(self):
        """
        We cannot change a jobdef as non-member
        """
        self.activate_user("non_member")
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


class TestJobDeleteAPI(BaseJobTestDef, APITestCase):
    """
    Test to delete a JobDef
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )

    def test_delete_as_anna(self):
        """
        By default, AskAnna user cannot delete jobs (not a member)
        """
        self.activate_user("anna")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_admin(self):
        """
        Delete a job as a workspace admin
        """
        self.activate_user("admin")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_member(self):
        """
        Delete a job as a workspace member
        """
        self.activate_user("member")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_nonmember(self):
        """
        Non workspace members cannot delete jobs
        """
        self.activate_user("non_member")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_anonymous(self):
        """
        Anonymous users cannot delete jobs
        """
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
