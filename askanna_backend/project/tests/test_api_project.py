# -*- coding: utf-8 -*-
"""Define tests for API of invitation workflow."""
import re

import pytest
from core.tests.base import BaseUserPopulation
from django.conf import settings
from django.urls import re_path, reverse
from django.views.static import serve
from job.models import JobDef, JobOutput, JobPayload, JobRun
from rest_framework import status
from rest_framework.test import APITestCase
from workspace.models import Workspace

import config.urls

from ..models import Project

pytestmark = pytest.mark.django_db


class BaseProjectTest(BaseUserPopulation, APITestCase):
    databases = ["default", "runinfo"]

    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name="test project", workspace=self.workspace_a)
        self.project_public = Project.objects.create(
            name="test project public", workspace=self.workspace_a, visibility="PUBLIC"
        )

        self.unused_workspace = Workspace.objects.create(name="unused workspace")
        self.unused_project = Project.objects.create(name="unused project", workspace=self.unused_workspace)

        self.private_project_in_public_workspace = Project.objects.create(
            name="test project private", workspace=self.workspace_c
        )
        self.project_public_in_public_workspace = Project.objects.create(
            name="test project public in public workspace",
            workspace=self.workspace_c,
            visibility="PUBLIC",
        )


class TestProjectListAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={"version": "v1"},
        )

    def test_list_project_as_admin(self):
        """An admin of the workspace can list projects"""
        self.activate_user("admin")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.project.short_uuid in str(response.content))
        self.assertFalse(self.unused_project.short_uuid in str(response.content))

    def test_list_project_as_member(self):
        """A member of the workspace can get list projects."""
        self.activate_user("member")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.project.short_uuid in str(response.content))
        self.assertFalse(self.unused_project.short_uuid in str(response.content))

        for r in response.data:
            # make sure we have an "is_member" for each workspace
            self.assertFalse(r.get("is_member") is None)

    def test_list_project_as_nonmember(self):
        """Non member do not have access to the workspace and thus cannot list projects of it."""
        self.activate_user("non_member")

        response = self.client.get(self.url, format="json")
        # The following is a bit counter intuitive, the non-member should still be able
        # to list other projects to which he/she has access to
        # in our testcase, the result is an empty list
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for project in response.data:
            self.assertEqual(project.get("visibility"), "PUBLIC")

        self.assertFalse(self.project.short_uuid in str(response.content))
        self.assertFalse(self.unused_project.short_uuid in str(response.content))

    def test_list_project_as_anonymous(self):
        """
        An anonymous user do not have access the workspace and thus cannot list projects of it.
        """
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for project in response.data:
            self.assertEqual(project.get("visibility"), "PUBLIC")


class TestProjectDetailAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )
        self.url_public_project = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project_public.short_uuid,
            },
        )

    def test_member_can_get_project(self):
        """A member of the workspace can get a project."""
        self.activate_user("member")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"short_uuid": self.project.short_uuid}.items() <= dict(response.data).items())

    def test_admin_can_get_project(self):
        """An admin of the workspace can get a project."""
        self.activate_user("admin")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"short_uuid": self.project.short_uuid}.items() <= dict(response.data).items())

    def test_non_member_cannot_get_project(self):
        """Non member do not have access to the project."""
        self.activate_user("non_member")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_get_private_project(self):
        """An anonymous user can only list public projects, but the project we want to access is not public."""
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_get_public_project_in_private_workspace(self):
        """An anonymous user can only list public projects, the project we access is public"""
        response = self.client.get(self.url_public_project, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestProjectCreateAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_member_can_create_project(self):
        """A member of the workspace can create a project."""
        self.activate_user("member")

        response = self.client.post(
            self.url,
            {"workspace": self.workspace_a.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_create_project(self):
        """An admin of the workspace can create a project."""
        self.activate_user("admin")

        response = self.client.post(
            self.url,
            {"workspace": self.workspace_a.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_member_cannot_create_project(self):
        """Non member can not create projects."""
        self.activate_user("non_member")

        response = self.client.post(
            self.url,
            {"workspace": self.workspace_a.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_create_project(self):
        """An anonymous user cannot create projects."""
        response = self.client.post(
            self.url,
            {"workspace": self.workspace_a.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_project_public(self):
        """An admin of the workspace can create a project."""
        self.activate_user("admin")

        response = self.client.post(
            self.url,
            {
                "name": "new created project",
                "workspace": self.workspace_a.short_uuid,
                "visibility": "PUBLIC",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue({"visibility": "PUBLIC"}.items() <= dict(response.data).items())


class TestProjectUpdateAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )

    def test_member_cannot_update_project(self):
        """A member of the workspace can not update info of a project."""
        self.activate_user("member")

        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace_a.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_project(self):
        """An admin of the workspace can update a project."""
        self.activate_user("admin")

        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace_a.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a new name"}.items() <= dict(response.data).items())

    def test_non_member_cannot_update_project(self):
        """Non member can not update a project."""
        self.activate_user("non_member")

        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace_a.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_update_project(self):
        """An anonymous user can not update a project."""
        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace_a.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_partially_update_project(self):
        """A member of the workspace can not partially update a project."""
        self.activate_user("member")

        response = self.client.patch(self.url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_partially_update_project(self):
        """An admin of the workspace can partially update a project."""
        self.activate_user("admin")

        response = self.client.patch(self.url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a partial new name"}.items() <= dict(response.data).items())

    def test_non_member_cannot_partially_update_project(self):
        """Non member can not partially update a project."""
        self.activate_user("non_member")

        response = self.client.patch(self.url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_partially_update_project(self):
        """An anonymous user can not partially update a project."""
        response = self.client.patch(self.url, {"name": "a partial new name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_set_public_project(self):
        """
        The admin can set a project to public
        """
        self.activate_user("admin")

        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"visibility": "PUBLIC"}.items() <= dict(response.data).items())

    def test_member_set_public_project(self):
        """
        Members cannot update project visibliity
        """
        self.activate_user("member")

        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonmember_set_public_project(self):
        """
        non-members cannot update project visibliity
        """
        self.activate_user("non_member")

        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_set_public_project(self):
        """
        Anonymous users cannot update project visibliity
        """
        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_set_public_project_typo(self):
        """
        Admin member setting an incorrect visibility raises an error
        """
        self.activate_user("admin")

        response = self.client.patch(self.url, {"visibility": "PUBLICTYPO"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestProjectDeleteAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.project.short_uuid,
            },
        )
        self.setUpDelete()

    def setUpDelete(self):
        self.original_urls = config.urls.urlpatterns
        config.urls.urlpatterns += [
            re_path(
                r"^%s(?P<path>.*)$" % re.escape("/files/".lstrip("/")),
                serve,
                kwargs={"document_root": str(settings.ROOT_DIR("storage_root"))},
            )
        ]

        self.activate_user("admin")

        # setup a job for the project
        self.job = JobDef.objects.create(
            name="test-job",
            project=self.project,
        )

        # our payload
        self.payload = {"test": 1, "format": "json", "user": "askanna"}

        # setup a payload for the project
        job_url = reverse("run-job", kwargs={"version": "v1", "short_uuid": self.job.short_uuid})
        response = self.client.post(
            job_url,
            self.payload,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job_run_suuid = response.data.get("short_uuid")

        # Fix issue for a job that was not run, so create output
        self.jobrun = JobRun.objects.get(short_uuid=job_run_suuid)
        self.jobpayload = JobPayload.objects.get(jobdef__pk=self.job.pk)
        self.joboutput = JobOutput.objects.get(jobrun=self.jobrun)
        self.joboutput.exit_code = 0
        self.joboutput.stdout = []
        self.joboutput.save()

        # reset credentials
        self.client.credentials()

    def tearDown(self):
        super().tearDown()
        config.urls.urlpatterns = self.original_urls

    def test_delete_as_admin(self):
        """
        An admin can remove a project
        """
        self.activate_user("admin")

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # delete it again will result in not found, because we don't expose it anymore
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_member(self):
        """
        A member of a project can not remove a project
        """
        self.activate_user("member")

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_nonmember(self):
        """
        A non-member of a project can not remove a project
        """
        self.activate_user("non_member")

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_anonymous(self):
        """
        An anonymous user cannot remove a project
        """
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestWorkspaceProjectListAPI(TestProjectListAPI):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-project-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace_a.short_uuid,
            },
        )

    def test_list_project_as_anonymous(self):
        """An anonymous user do not have access the workspace and thus cannot list projects of it.
        We only have 1 public project listed
        """
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for project in response.data:
            self.assertEqual(project.get("visibility"), "PUBLIC")

    def test_list_project_as_nonmember(self):
        """Non member do not have access to the workspace and thus cannot list projects of it.
        In this case we already pre-select for which workspace by url"""
        self.activate_user("non_member")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestProjectListWithFilterAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={"version": "v1"},
        )

    def test_list_as_anna(self):
        """
        By default Anna should only list public projects only
        """
        self.activate_user("anna")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_admin(self):
        """
        List the workspace as an admin of the workspace a, but also member of b
        """
        self.activate_user("admin")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # also test ordering, possible with test admin account as this has 3 workspaces to list all
        response = self.client.get(self.url, {"ordering": "membership"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(self.url, {"ordering": "-membership"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(self.url, {"ordering": "-membership,-created"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_as_member(self):
        """A member gets only projects from workspace membership and public projects"""
        self.activate_user("member")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # also test ordering, also possible with test member account as this has 3 workspaces to list all
        response = self.client.get(self.url, {"ordering": "membership"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(self.url, {"ordering": "-membership"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(self.url, {"ordering": "-membership,-created"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_as_non_member(self):
        """A user will only see public projects"""
        self.activate_user("non_member")

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_anonymous(self):
        """A anonymous user will only see public project in the list."""

        response = self.client.get(self.url, {"membership": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "False"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {"membership": "yes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {"membership": "no"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
