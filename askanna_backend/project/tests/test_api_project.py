"""Define tests for API of invitation workflow."""
import json
import os
import pytest
import re

from django.conf import settings
from django.urls import reverse, re_path
from django.views.static import serve
from rest_framework import status
from rest_framework.test import APITestCase

import config.urls
from job.models import JobDef, JobRun, JobOutput, JobPayload
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, User, UserProfile
from workspace.models import Workspace

from ..models import Project

pytestmark = pytest.mark.django_db


class BaseProjectTest(APITestCase):
    def setUp(self):
        self.users = {
            "admin_a": User.objects.create(
                username="admin_a", is_staff=True, is_superuser=True
            ),
            "member_a": User.objects.create(username="member_a"),
            "user_a": User.objects.create(username="user_a"),
        }
        self.workspace = Workspace.objects.create(title="test workspace")
        self.project = Project.objects.create(
            name="test project", workspace=self.workspace
        )

        self.unused_workspace = Workspace.objects.create(title="unused workspace")
        self.unused_project = Project.objects.create(
            name="unused project", workspace=self.unused_workspace
        )

        # make the admin user member of the workspace
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin_a"],
            role=WS_ADMIN,
        )
        # make the member_a user member of the workspace
        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
        )


class TestProjectListAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("project-list", kwargs={"version": "v1"},)

    def test_list_project_as_admin(self):
        """An admin of the workspace can list projects"""
        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.project.short_uuid in str(response.content))
        self.assertFalse(self.unused_project.short_uuid in str(response.content))

    def test_list_project_as_member(self):
        """A member of the workspace can get list projects."""
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.project.short_uuid in str(response.content))
        self.assertFalse(self.unused_project.short_uuid in str(response.content))

    def test_list_project_as_nonmember(self):
        """Non member do not have access to the workspace and thus cannot list projects of it."""
        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        # The following is a bit counter intuitive, the non-member should still be able
        # to list other projects to which he/she has access to
        # in our testcase, the result is an empty list
        self.assertEqual(response.data, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.project.short_uuid in str(response.content))
        self.assertFalse(self.unused_project.short_uuid in str(response.content))

    def test_list_project_as_anonymous(self):
        """An anonymous user do not have access the workspace and thus cannot list projects of it."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectDetailAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={"version": "v1", "short_uuid": self.project.short_uuid,},
        )

    def test_member_can_get_project(self):
        """A member of the workspace can get a project."""
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.project.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_admin_can_get_project(self):
        """An admin of the workspace can get a project."""
        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.project.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_non_member_cannot_get_project(self):
        """Non member do not have access to the project."""
        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_get_project(self):
        """An anonymous user do not have access to the project."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectCreateAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("project-list", kwargs={"version": "v1",},)

    def test_member_can_create_project(self):
        """A member of the workspace can create a project."""
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {"workspace": self.workspace.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_create_project(self):
        """An admin of the workspace can create a project."""
        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {"workspace": self.workspace.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_member_cannot_create_project(self):
        """Non member can not create projects."""
        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            self.url,
            {"workspace": self.workspace.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_create_project(self):
        """An anonymous user cannot create projects."""
        response = self.client.post(
            self.url,
            {"workspace": self.workspace.short_uuid, "name": "new created project"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectUpdateAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={"version": "v1", "short_uuid": self.project.short_uuid,},
        )

    def test_member_can_update_project(self):
        """A member of the workspace can update a project."""
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a new name"}.items() <= dict(response.data).items())

    def test_admin_can_update_project(self):
        """An admin of the workspace can update a project."""
        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({"name": "a new name"}.items() <= dict(response.data).items())

    def test_non_member_cannot_update_project(self):
        """Non member can not update a project."""
        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_update_project(self):
        """An anonymous user can not update a project."""
        response = self.client.put(
            self.url,
            {"name": "a new name", "workspace": self.workspace.short_uuid},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_partially_update_project(self):
        """A member of the workspace can partially update a project."""
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url, {"name": "a partial new name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"name": "a partial new name"}.items() <= dict(response.data).items()
        )

    def test_admin_can_partially_update_project(self):
        """An admin of the workspace can partially update a project."""
        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url, {"name": "a partial new name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"name": "a partial new name"}.items() <= dict(response.data).items()
        )

    def test_non_member_cannot_partially_update_project(self):
        """Non member can not partially update a project."""

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url, {"name": "a partial new name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_partially_update_project(self):
        """An anonymous user can not partially update a project."""
        response = self.client.patch(
            self.url, {"name": "a partial new name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectDeleteAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={"version": "v1", "short_uuid": self.project.short_uuid,},
        )

        self.original_urls = config.urls.urlpatterns
        config.urls.urlpatterns += [
            re_path(
                r"^%s(?P<path>.*)$" % re.escape("/files/".lstrip("/")),
                serve,
                kwargs={"document_root": str(settings.ROOT_DIR("storage_root"))},
            )
        ]

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        # setup a job for the project
        self.job = JobDef.objects.create(name="test-job", project=self.project,)

        # our payload
        self.payload = {"test": 1, "format": "json", "user": "askanna"}

        # setup a payload for the project
        job_url = reverse("run-job", kwargs={"short_uuid": self.job.short_uuid})
        response = self.client.post(
            job_url, self.payload, format="json", HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job_run_suuid = response.data.get("run_uuid")

        # Fix issue for a job that was not run, so create output
        self.jobrun = JobRun.objects.get(short_uuid=job_run_suuid)
        self.jobpayload = JobPayload.objects.get(jobdef__pk=self.job.pk)
        self.joboutput = JobOutput.objects.get(jobrun=self.jobrun)
        self.joboutput.exit_code = 0
        self.joboutput.stdout = []
        self.joboutput.save()

        # TODO: setup code for the project

        # TODO: setup a run that creates an artifact

        # reset credentials
        self.client.credentials()

        # other urls to check
        self.payload_json_url = str(self.jobpayload.stored_path).replace(
            str(settings.STORAGE_ROOT), "/files",
        )
        self.payload_exists()

    def tearDown(self):
        super().tearDown()
        config.urls.urlpatterns = self.original_urls

    def payload_is_gone(self):
        # now the payload should not be there anymore
        response = self.client.get(self.payload_json_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def payload_exists(self):
        response = self.client.get(self.payload_json_url)
        self.assertEqual(json.loads(response.getvalue().decode("utf-8")), self.payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_as_admin(self):
        """
        An admin can remove a project
        """

        token = self.users["admin_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.payload_is_gone()

    def test_delete_as_member(self):
        """
        A member of a project can remove a project
        """

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.payload_is_gone()

    def test_delete_as_nonmember(self):
        """
        A non-member of a project can not remove a project
        """

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.payload_exists()

    def test_delete_as_anonymous(self):

        """
        An anonymous user cannot remove a project
        """
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.payload_exists()
