from unittest.mock import Mock, PropertyMock

import pytest
from django.test import RequestFactory, TestCase
from rest_framework import mixins, serializers

from core.permissions.askanna import AskAnnaPermissionByAction
from core.permissions.role_utils import (
    get_request_roles,
    get_user_role,
    get_user_roles_for_project,
    get_user_workspace_role,
    request_has_permission,
)
from core.permissions.roles import (
    AskAnnaAdmin,
    AskAnnaMember,
    AskAnnaPublicViewer,
    ProjectAdmin,
    ProjectMember,
    ProjectNoMember,
    ProjectPublicViewer,
    WorkspaceAdmin,
    WorkspaceMember,
    WorkspaceNoMember,
    WorkspacePublicViewer,
)
from core.views import AskAnnaGenericViewSet

pytestmark = pytest.mark.django_db


PermissionModel = Mock()
PermissionModel.request_has_read_permission.return_value = True

DuplicatePermissionModel = Mock()
type(DuplicatePermissionModel).permission_by_action = PropertyMock(return_value={"list": "project.code.list"})
DuplicatePermissionModel.request_has_read_permission.return_value = True


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionModel
        fields = "__all__"


class PermissionViewSet(mixins.ListModelMixin, AskAnnaGenericViewSet):
    serializer_class = PermissionSerializer
    detail = False


class DuplicatePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuplicatePermissionModel
        fields = "__all__"


class DuplicatePermissionViewSet(mixins.ListModelMixin, AskAnnaGenericViewSet):
    serializer_class = DuplicatePermissionSerializer
    detail = False


class TestAskAnnaPermissionByAction(TestCase):
    def test_askanna_permission_get_permission_by_action(self):
        obj = Mock()
        obj.permission_by_action = {
            "list": "project.code.list",
            ("retrieve", "info", "download"): "project.code.view",
        }
        permission = AskAnnaPermissionByAction()

        assert permission._get_permission(obj, "list") == "project.code.list"
        assert permission._get_permission(obj, "info") == "project.code.view"

        with pytest.raises(KeyError):
            permission._get_permission(obj, "create")

    def test_askanna_permission_has_permission(self):
        factory = RequestFactory()
        request = factory.get("/some-url")

        view = PermissionViewSet()
        permission = AskAnnaPermissionByAction()

        assert permission.has_permission(request, view) is True

        view = DuplicatePermissionViewSet()
        with pytest.warns(UserWarning):
            assert permission.has_permission(request, view) is True

    def test_askanna_permission_has_object_permission(self):
        factory = RequestFactory()
        request = factory.get("/some-url")

        view = PermissionViewSet()
        permission = AskAnnaPermissionByAction()

        obj = Mock()
        obj.request_has_object_read_permission = Mock(return_value=True)

        assert permission.has_object_permission(request, view, obj) is True

        obj.permission_by_action = {
            "list": "project.code.list",
        }

        with pytest.warns(UserWarning):
            assert permission.has_object_permission(request, view, obj) is True


class TestPermissionRoleUtils:
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_workspaces, test_projects, test_memberships):
        self.users = test_users
        self.workspaces = test_workspaces
        self.projects = test_projects

    def test_get_user_role(self):
        assert get_user_role(self.users["askanna_super_admin"]) == AskAnnaAdmin
        assert get_user_role(self.users["workspace_admin"]) == AskAnnaMember
        assert get_user_role(self.users["inactive_member"]) == AskAnnaPublicViewer

    def test_get_user_workspace_role(self):
        assert (
            get_user_workspace_role(self.users["askanna_super_admin"], self.workspaces["workspace_private"])
            == WorkspaceNoMember
        )
        assert (
            get_user_workspace_role(self.users["askanna_super_admin"], self.workspaces["workspace_public"])
            == WorkspacePublicViewer
        )

        assert (
            get_user_workspace_role(self.users["workspace_admin"], self.workspaces["workspace_private"])
            == WorkspaceAdmin
        )
        assert (
            get_user_workspace_role(self.users["workspace_member"], self.workspaces["workspace_private"])
            == WorkspaceMember
        )

        assert (
            get_user_workspace_role(self.users["inactive_member"], self.workspaces["workspace_private"])
            == WorkspaceNoMember
        )
        assert (
            get_user_workspace_role(self.users["inactive_member"], self.workspaces["workspace_public"])
            == WorkspacePublicViewer
        )

    def test_get_user_roles_for_project(self):
        assert get_user_roles_for_project(self.users["askanna_super_admin"], self.projects["project_private"]) == [
            WorkspaceNoMember,
            ProjectNoMember,
        ]
        assert get_user_roles_for_project(self.users["askanna_super_admin"], self.projects["project_public"]) == [
            WorkspacePublicViewer,
            ProjectPublicViewer,
        ]

        assert get_user_roles_for_project(self.users["workspace_admin"], self.projects["project_private"]) == [
            WorkspaceAdmin,
            ProjectAdmin,
        ]
        assert get_user_roles_for_project(self.users["workspace_member"], self.projects["project_private"]) == [
            WorkspaceMember,
            ProjectMember,
        ]

        assert get_user_roles_for_project(self.users["inactive_member"], self.projects["project_private"]) == [
            WorkspaceNoMember,
            ProjectNoMember,
        ]
        assert get_user_roles_for_project(self.users["inactive_member"], self.projects["project_public"]) == [
            WorkspacePublicViewer,
            ProjectPublicViewer,
        ]

    def test_get_request_roles(self):
        assert get_request_roles(Mock(user=self.users["askanna_super_admin"])) == [AskAnnaAdmin]
        assert get_request_roles(Mock(user=self.users["workspace_admin"])) == [AskAnnaMember]
        assert get_request_roles(Mock(user=self.users["inactive_member"])) == [AskAnnaPublicViewer]

        assert get_request_roles(
            Mock(user=self.users["askanna_super_admin"]), project=self.projects["project_private"]
        ) == [AskAnnaAdmin, WorkspaceNoMember, ProjectNoMember]
        assert get_request_roles(
            Mock(user=self.users["askanna_super_admin"]), project=self.projects["project_public"]
        ) == [AskAnnaAdmin, WorkspacePublicViewer, ProjectPublicViewer]

        assert get_request_roles(
            Mock(user=self.users["workspace_admin"]), workspace=self.workspaces["workspace_private"]
        ) == [AskAnnaMember, WorkspaceAdmin]

        assert get_request_roles(
            Mock(user=self.users["workspace_admin"]),
            project=self.projects["project_private"],
            workspace=self.workspaces["workspace_private"],
        ) == [AskAnnaMember, WorkspaceAdmin, ProjectAdmin]

        with pytest.raises(AssertionError):
            get_request_roles(
                Mock(user=self.users["workspace_member"]),
                project=self.projects["project_public"],
                workspace=self.workspaces["workspace_private"],
            )

    def test_request_has_permission(self):
        assert request_has_permission(
            Mock(user=self.users["workspace_member"]),
            permission="project.create",
            project=self.projects["project_private"],
        )
