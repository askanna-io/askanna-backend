import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Project
from core.tests.base import BaseUserPopulation
from workspace.models import Workspace

pytestmark = pytest.mark.django_db


class BaseProjectTest(BaseUserPopulation, APITestCase):
    def setUp(self):
        super().setUp()

        self.project = Project.objects.create(
            name="test project",
            workspace=self.workspace_a,
            created_by_user=self.workspace_a.created_by_user,
        )
        self.project_public = Project.objects.create(
            name="test project public",
            workspace=self.workspace_a,
            created_by_user=self.workspace_a.created_by_user,
            visibility="PUBLIC",
        )

        self.unused_workspace = Workspace.objects.create(
            name="unused workspace",
            created_by_user=self.workspace_c.created_by_user,
        )
        self.unused_project = Project.objects.create(
            name="unused project",
            workspace=self.unused_workspace,
            created_by_user=self.unused_workspace.created_by_user,
        )

        self.private_project_in_public_workspace = Project.objects.create(
            name="test project private",
            workspace=self.workspace_c,
            created_by_user=self.workspace_c.created_by_user,
        )
        self.project_public_in_public_workspace = Project.objects.create(
            name="test project public in public workspace",
            workspace=self.workspace_c,
            created_by_user=self.workspace_c.created_by_user,
            visibility="PUBLIC",
        )


class TestProjectListAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={"version": "v1"},
        )

    def test_list_project_as_anna(self):
        """An AskAnna admin does not have access to the workspace and thus cannot list projects of it."""
        self.activate_user("anna")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore
        assert self.project.suuid not in str(response.content)
        assert self.unused_project.suuid not in str(response.content)

        for project in response.data["results"]:  # type: ignore
            assert project["visibility"] == "PUBLIC"

    def test_list_project_as_admin(self):
        """An admin of the workspace can list projects"""
        self.activate_user("admin")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 7  # type: ignore
        assert self.project.suuid in str(response.content)
        assert self.unused_project.suuid not in str(response.content)

    def test_list_project_as_member(self):
        """A member of the workspace can get list projects."""
        self.activate_user("member")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 6  # type: ignore
        assert self.project.suuid in str(response.content)
        assert self.unused_project.suuid not in str(response.content)

    def test_list_project_as_non_member(self):
        """Non member do not have access to the workspace and thus cannot list projects of it."""
        self.activate_user("non_member")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore
        assert self.project.suuid not in str(response.content)
        assert self.unused_project.suuid not in str(response.content)

        for project in response.data["results"]:  # type: ignore
            assert project["visibility"] == "PUBLIC"

    def test_list_project_as_anonymous(self):
        """
        An anonymous user do not have access the workspace and thus cannot list projects of it.
        """
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore
        assert self.project.suuid not in str(response.content)
        assert self.unused_project.suuid not in str(response.content)

        for project in response.data["results"]:  # type: ignore
            assert project["visibility"] == "PUBLIC"


class TestProjectDetailAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "suuid": self.project.suuid,
            },
        )
        self.url_public_project = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "suuid": self.project_public.suuid,
            },
        )

    def test_anna_cannot_get_project(self):
        """An AskAnna admin do not have access to the project."""
        self.activate_user("anna")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_get_project(self):
        """An admin of the workspace can get a project."""
        self.activate_user("admin")

        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.project.suuid  # type: ignore

    def test_member_can_get_project(self):
        """A member of the workspace can get a project."""
        self.activate_user("member")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.project.suuid  # type: ignore

    def test_non_member_cannot_get_project(self):
        """Non-member do not have access to the project."""
        self.activate_user("non_member")
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_member_cannot_get_public_project_in_private_workspace(self):
        """Non-member can only list public projects in public workspaces"""
        response = self.client.get(self.url_public_project, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_user_cannot_get_private_project(self):
        """An anonymous user can only list public projects"""
        response = self.client.get(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_user_cannot_get_public_project_in_private_workspace(self):
        """An anonymous user can only list public projects in public workspaces"""
        response = self.client.get(self.url_public_project, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProjectCreateAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_anna_cannot_create_project(self):
        """An AskAnna admin can by default not create projects in a workspace"""
        self.activate_user("anna")
        response = self.client.post(
            self.url,
            {"workspace_suuid": self.workspace_a.suuid, "name": "new created project"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_create_project(self):
        """An admin of the workspace can create a project."""
        self.activate_user("admin")
        response = self.client.post(
            self.url,
            {"workspace_suuid": self.workspace_a.suuid, "name": "new created project"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_member_can_create_project(self):
        """A member of the workspace can create a project."""
        self.activate_user("member")
        response = self.client.post(
            self.url,
            {"workspace_suuid": self.workspace_a.suuid, "name": "new created project"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_non_member_cannot_create_project(self):
        """Non member can not create projects."""
        self.activate_user("non_member")
        response = self.client.post(
            self.url,
            {"workspace_suuid": self.workspace_a.suuid, "name": "new created project"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_user_cannot_create_project(self):
        """An anonymous user cannot create projects."""
        response = self.client.post(
            self.url,
            {"workspace_suuid": self.workspace_a.suuid, "name": "new created project"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_member_can_create_public_project_public(self):
        """A member of the workspace can create a project."""
        self.activate_user("member")
        response = self.client.post(
            self.url,
            {
                "workspace_suuid": self.workspace_a.suuid,
                "name": "new created project",
                "visibility": "PUBLIC",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["visibility"] == "PUBLIC"  # type: ignore


class TestProjectUpdateAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "suuid": self.project.suuid,
            },
        )

    def test_askanna_admin_cannot_update_project(self):
        """An AskAnna admin cannot update info of a project."""
        self.activate_user("anna")
        response = self.client.patch(self.url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_update_project(self):
        """An admin of the workspace can update a project."""
        self.activate_user("admin")
        response = self.client.patch(self.url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "a new name"  # type: ignore

    def test_member_cannot_update_project(self):
        """A member of the workspace cannot update info of a project."""
        self.activate_user("member")
        response = self.client.patch(self.url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_member_cannot_update_project(self):
        """Non member can not update a project."""
        self.activate_user("non_member")
        response = self.client.patch(self.url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_user_cannot_update_project(self):
        """An anonymous user can not update a project."""
        response = self.client.patch(self.url, {"name": "a new name"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_set_public_project(self):
        """The admin can set a project to public"""
        self.activate_user("admin")
        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["visibility"] == "PUBLIC"  # type: ignore

    def test_member_cannot_set_public_project(self):
        """Members cannot update project visibliity"""
        self.activate_user("member")
        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_member_cannot_set_public_project(self):
        """Non-members cannot update project visibility"""
        self.activate_user("non_member")
        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_cannot_set_public_project(self):
        """Anonymous users cannot update project visibliity"""
        response = self.client.patch(self.url, {"visibility": "PUBLIC"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_set_public_project_typo(self):
        """Admin member setting an incorrect visibility raises an error"""
        self.activate_user("admin")
        response = self.client.patch(self.url, {"visibility": "PUBLICTYPO"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["visibility"] == ['"PUBLICTYPO" is not a valid choice.']  # type: ignore


class TestProjectDeleteAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-detail",
            kwargs={
                "version": "v1",
                "suuid": self.project.suuid,
            },
        )

    def test_delete_as_askanna_admin(self):
        """AskAnna admin cannot remove a project"""
        self.activate_user("anna")
        response = self.client.delete(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_admin(self):
        """An admin can remove a project"""
        self.activate_user("admin")

        response = self.client.delete(self.url, format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Delete it again will result in not found, because we don't expose it anymore
        response = self.client.delete(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_member(self):
        """A member of a project can not remove a project"""
        self.activate_user("member")
        response = self.client.delete(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_non_member(self):
        """A non-member of a project can not remove a project"""
        self.activate_user("non_member")
        response = self.client.delete(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_anonymous(self):
        """An anonymous user cannot remove a project"""
        response = self.client.delete(self.url, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestWorkspaceProjectListAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_project_as_member(self):
        self.activate_user("member")

        response = self.client.get(
            self.url,
            {
                "workspace_suuid": self.workspace_a.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

    def test_list_project_as_anonymous(self):
        response = self.client.get(
            self.url,
            {
                "workspace_suuid": self.workspace_a.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_project_as_nonmember(self):
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            {
                "workspace_suuid": self.workspace_a.suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore


class TestProjectListWithFilterAPI(BaseProjectTest):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "project-list",
            kwargs={"version": "v1"},
        )

    def test_list_as_anna(self):
        self.activate_user("anna")

        response = self.client.get(self.url, {"is_member": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

        response = self.client.get(self.url, {"is_member": "false"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_admin(self):
        """List the workspace as an admin of the workspace a, but also this admin is member of workspace b"""
        self.activate_user("admin")

        response = self.client.get(self.url, {"is_member": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5  # type: ignore

        response = self.client.get(self.url, {"is_member": "false"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

        response = self.client.get(self.url, {"order_by": "is_member"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 7  # type: ignore

        response = self.client.get(self.url, {"order_by": "-is_member"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 7  # type: ignore

        response = self.client.get(self.url, {"order_by": "-is_member,-created_at"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 7  # type: ignore

    def test_list_as_member(self):
        self.activate_user("member")

        response = self.client.get(self.url, {"is_member": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

        response = self.client.get(self.url, {"is_member": "false"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_non_member(self):
        self.activate_user("non_member")

        response = self.client.get(self.url, {"is_member": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

        response = self.client.get(self.url, {"is_member": "false"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_anonymous(self):
        response = self.client.get(self.url, {"is_member": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

        response = self.client.get(self.url, {"is_member": "false"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore
