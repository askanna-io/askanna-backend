import pytest

from account.models.membership import MSP_WORKSPACE, Membership
from core.permissions.askanna_roles import (
    AskAnnaMember,
    WorkspaceAdmin,
    WorkspaceMember,
)
from tests.utils import get_avatar_content_file


def test_get_role_workspace_admin(test_memberships):
    assert test_memberships["workspace_private_admin"].get_role() == WorkspaceAdmin


def test_get_role_workspace_member(test_memberships):
    assert test_memberships["workspace_private_member"].get_role() == WorkspaceMember


def test_get_role_that_does_not_exist(test_users, test_workspaces):
    membership = Membership.objects.create(
        user=test_users.get("workspace_member"),
        object_uuid=test_workspaces.get("workspace_private").uuid,
        object_type=MSP_WORKSPACE,
        role=AskAnnaMember.code,
    )
    with pytest.raises(ValueError):
        membership.get_role()

    membership.delete()


def test_get_active_member(test_memberships):
    assert Membership.objects.active_members().count() == 3  # type: ignore
    test_memberships["workspace_private_admin"].to_deleted()
    assert Membership.objects.active_members().count() == 2  # type: ignore


def test_get_is_active_workspace_member(test_memberships):
    assert test_memberships["workspace_private_member"].is_active is True

    test_memberships["workspace_private_member"].to_deleted()
    assert test_memberships["workspace_private_member"].is_active is False


def test_avatar_directory(test_memberships):
    member = test_memberships.get("workspace_private_admin")
    assert "avatars" in member.avatar_directory


def test_membership_set_avatar(test_memberships):
    member = test_memberships.get("workspace_private_admin")
    assert member.get_avatar_files() is None

    member.set_avatar(get_avatar_content_file())
    assert member.avatar_files.count() == 5


def test_membership_delete_avatar_files(test_memberships):
    member = test_memberships.get("workspace_private_admin")

    member.set_avatar(get_avatar_content_file())
    assert member.avatar_files.count() == 5

    member.delete_avatar_files()
    assert member.delete_avatar_files() is not None
    assert member.avatar_files.count() == 0

    member = test_memberships.get("workspace_private_member")
    assert member.avatar_files is None
    assert member.delete_avatar_files() is None


def test_membership_to_deleted(test_users, test_memberships):
    user = test_users["workspace_admin"]
    membership = test_memberships.get("workspace_private_admin")

    user.set_avatar(get_avatar_content_file())

    assert membership.deleted_at is None
    assert membership.name == "workspace private admin"
    assert membership.avatar_files is None
    assert membership.use_global_profile is True
    assert membership.get_name() == "workspace admin"
    assert membership.get_avatar_files().count() == 5

    assert user.name == "workspace admin"
    assert user.email.startswith("deleted-") is False
    assert user.avatar_files.count() == 5

    membership.to_deleted()

    assert user.name == "workspace admin"
    assert user.email.startswith("deleted-") is False
    assert user.avatar_files.count() == 5

    assert membership.deleted_at is not None
    assert membership.name == "workspace admin"
    assert membership.avatar_files.count() == 5
    assert membership.use_global_profile is False
    assert membership.get_name() == "workspace admin"
    assert membership.get_avatar_files().count() == 5


def test_membership_with_object_type_not_workspace(test_users, test_workspaces):
    membership = Membership.objects.create(
        user=test_users.get("workspace_member"),
        object_uuid=test_workspaces.get("workspace_private").uuid,
        object_type="PS",
        role=AskAnnaMember.code,
    )
    assert membership.workspace is None
    membership.delete()
