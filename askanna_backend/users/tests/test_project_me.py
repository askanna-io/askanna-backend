# -*- coding: utf-8 -*-
from .test_global_me import BaseTestGlobalMeGet
from .test_workspace_me import WorkspaceTestSet

from django.urls import reverse
import pytest
from rest_framework import status
from rest_framework.test import APITestCase

from project.models import Project

pytestmark = pytest.mark.django_db


class ProjectTestSet(WorkspaceTestSet):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name="test project", workspace=self.workspace)
        self.project_public = Project.objects.create(
            name="test project public",
            workspace=self.workspace_public,
            visibility="PUBLIC",
        )

        self.url = reverse(
            "project-me",
            kwargs={
                "short_uuid": self.project.short_uuid,
            },
        )

        self.url_non_exist = reverse(
            "project-me",
            kwargs={
                "short_uuid": self.project.short_uuid[:-1] + "1",
            },
        )


class TestProjectMeGet(ProjectTestSet, BaseTestGlobalMeGet, APITestCase):
    def test_me_as_anna(self):
        """
        Anna doesn't have acces to the project
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_as_anonymous(self):
        """
        An anonymous user cannot get /me on a private workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestProjectPublicMeGet(ProjectTestSet, BaseTestGlobalMeGet, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-me",
            kwargs={
                "short_uuid": self.project_public.short_uuid,
            },
        )

    def test_me_as_anna(self):
        """
        Anna has all access
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
