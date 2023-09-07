import pytest

from workspace.models import Workspace


def test_create_workspace(test_users):
    Workspace.objects.create(name="test workspace private", created_by=test_users["workspace_admin"])


def test_create_workspace_without_creator_fails(db):
    with pytest.raises(ValueError):
        Workspace.objects.create(name="test workspace private")


def test_object_active(test_workspaces):
    assert Workspace.objects.active().count() == 2  # type: ignore
    test_workspaces["workspace_private"].to_deleted()
    assert Workspace.objects.active().count() == 1  # type: ignore


def test_object_inactive(test_workspaces):
    assert Workspace.objects.inactive().count() == 0  # type: ignore
    test_workspaces["workspace_private"].to_deleted()
    assert Workspace.objects.inactive().count() == 1  # type: ignore


def test_workspace_visibility_private(test_workspaces):
    workspace = test_workspaces["workspace_private"]
    assert workspace.visibility == "PRIVATE"
    assert workspace.is_private is True
    assert workspace.is_public is False


def test_workspace_visibility_public(test_workspaces):
    workspace = test_workspaces["workspace_public"]
    assert workspace.visibility == "PUBLIC"
    assert workspace.is_private is False
    assert workspace.is_public is True
