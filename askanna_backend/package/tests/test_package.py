import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from job.tests.base import BaseJobTestDef

pytestmark = pytest.mark.django_db


class TestPackageList(BaseJobTestDef, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_admin(self):
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

    def test_list_as_member(self):
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_anonymous(self):
        """
        Anonymous can only list packages from public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore


class TestProjectPackageList(BaseJobTestDef, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_admin(self):
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_member(self):
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_anonymous(self):
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore


class TestPublicProjectPackageList(BaseJobTestDef, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project3.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_admin(self):
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project3.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_member(self):
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project3.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project3.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore

    def test_list_as_anonymous(self):
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.project3.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # type: ignore
