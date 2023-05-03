import pytest

from account.models.membership import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership
from core.permissions.askanna_roles import (
    AskAnnaMember,
    WorkspaceAdmin,
    WorkspaceMember,
)


def test_get_role_workspace_admin(test_users, test_workspaces):
    membership = Membership.objects.create(
        user=test_users.get("workspace_admin"),
        object_uuid=test_workspaces.get("workspace_private").uuid,
        object_type=MSP_WORKSPACE,
        role=WS_ADMIN,
    )
    assert membership.get_role() == WorkspaceAdmin


def test_get_role_workspace_member(test_users, test_workspaces):
    membership = Membership.objects.create(
        user=test_users.get("workspace_member"),
        object_uuid=test_workspaces.get("workspace_private").uuid,
        object_type=MSP_WORKSPACE,
        role=WS_MEMBER,
    )
    assert membership.get_role() == WorkspaceMember


def test_get_role_that_does_not_exist(test_users, test_workspaces):
    membership = Membership.objects.create(
        user=test_users.get("workspace_member"),
        object_uuid=test_workspaces.get("workspace_private").uuid,
        object_type=MSP_WORKSPACE,
        role=AskAnnaMember.code,
    )
    with pytest.raises(ValueError):
        membership.get_role()
