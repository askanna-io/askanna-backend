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

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_nonmember(self):
        """
        We can list job as member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_anonymous(self):
        """
        Anonymous user can only list public projects
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class TestProjectJobListAPI(TestJobListAPI):
    """
    Test to list the JobDefs in a project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-job-list",
            kwargs={
                "version": "v1",
                "parent_lookup_project__suuid": self.project.suuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_nonmember(self):
        """
        We can list job as member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_anonymous(self):
        """
        Anonymous users cannot list from private project
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class TestJobDetailAPI(BaseJobTestDef, APITestCase):

    """
    Test to get details of a Jobdefs
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )

    def test_detail_as_admin(self):
        """
        We can get details of a jobdef as an admin
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("suuid") == self.jobdef.suuid)

    def test_detail_as_member(self):
        """
        We can get details of a jobdef as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("suuid") == self.jobdef.suuid)

    def test_detail_as_nonmember(self):
        """
        We can NOT get details of a jobdef as non-member
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_anonymous(self):
        """
        We can NOT get details of a run as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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

    def test_change_as_admin(self):
        """
        We can get changes of a jobdef as an admin
        """
        self.activate_user("admin")

        change_job_payload = {
            "name": "newname",
            "description": "test",
        }

        response = self.client.patch(
            self.url,
            change_job_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("suuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("description") == "test")
        self.assertTrue(response.data.get("suuid") == self.jobdef.suuid)

    def test_change_as_member(self):
        """
        We can get changes of a jobdef as a member
        """
        self.activate_user("member")

        change_job_payload = {
            "name": "newname",
            "description": "test",
        }

        response = self.client.patch(
            self.url,
            change_job_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("suuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("description") == "test")
        self.assertTrue(response.data.get("suuid") == self.jobdef.suuid)

    def test_change_as_nonmember(self):
        """
        We can NOT get changes of a jobdef as non-member
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_as_anonymous(self):
        """
        We can NOT get changes of a run as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestJobDeleteAPI(BaseJobTestDef, APITestCase):
    """
    Test the deletion of the job
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

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_admin(self):
        """
        Delete a job as an workspace admin
        """
        self.activate_user("admin")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_as_member(self):
        """
        Delete a job as an workspace member
        """
        self.activate_user("member")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_as_nonmember(self):
        """
        Non workspace members cannot delete jobs
        """
        self.activate_user("non_member")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_anonymous(self):
        """
        Anonymous users cannot delete
        """

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
