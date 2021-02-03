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
        self.url = reverse("job-list", kwargs={"version": "v1"},)

    def test_list_as_admin(self):
        """
        We can list job as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_nonmember(self):
        """
        We can list job as member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We can list job as member of a workspace
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectJobListAPI(TestJobListAPI):
    """
    Test to list the JobDefs in a project
    """

    def setUp(self):
        self.url = reverse(
            "project-job-list",
            kwargs={
                "version": "v1",
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )

    def test_list_as_member(self):
        """
        We can list job as member of a workspace
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_nonmember(self):
        """
        We can list job as member of a workspace
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestJobDetailAPI(BaseJobTestDef, APITestCase):

    """
    Test to get details of a Jobdefs
    """

    def setUp(self):
        self.url = reverse(
            "job-detail",
            kwargs={"version": "v1", "short_uuid": self.jobdef.short_uuid},
        )

    def test_detail_as_admin(self):
        """
        We can get details of a jobdef as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobdef.short_uuid)

    def test_detail_as_member(self):
        """
        We can get details of a jobdef as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobdef.short_uuid)

    def test_detail_as_nonmember(self):
        """
        We can NOT get details of a jobdef as non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_anonymous(self):
        """
        We can NOT get details of a jobrun as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectJobDetailAPI(TestJobDetailAPI):

    """
    Test to get details of a Jobdefs
    """

    def setUp(self):
        self.url = reverse(
            "project-job-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobdef.short_uuid,
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )


class TestJobChangeAPI(BaseJobTestDef, APITestCase):

    """
    Test to change a Jobdef
    """

    def setUp(self):
        self.url = reverse(
            "job-detail",
            kwargs={"version": "v1", "short_uuid": self.jobdef.short_uuid},
        )

    def test_change_as_admin(self):
        """
        We can get changes of a jobdef as an admin
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_job_payload = {
            "name": "newname",
            "description": "test",
        }

        response = self.client.patch(self.url, change_job_payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("description") == "test")
        self.assertTrue(response.data.get("short_uuid") == self.jobdef.short_uuid)

    def test_change_as_member(self):
        """
        We can get changes of a jobdef as a member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_job_payload = {
            "name": "newname",
            "description": "test",
        }

        response = self.client.patch(self.url, change_job_payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("description") == "test")
        self.assertTrue(response.data.get("short_uuid") == self.jobdef.short_uuid)

    def test_change_as_nonmember(self):
        """
        We can NOT get changes of a jobdef as non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_as_anonymous(self):
        """
        We can NOT get changes of a jobrun as anonymous
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
