import pytest

from account.models.membership import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership
from account.models.user import User
from job.models import JobDef
from project.models import Project
from workspace.models import Workspace


@pytest.fixture()
def test_users(db) -> dict:
    return {
        "askanna_super_admin": User.objects.create_superuser(  # nosec: B106
            username="askanna_super_admin",
            is_staff=True,
            is_superuser=True,
            email="admin@example.com",
            password="password-admin",
            name="admin",
        ),
        "workspace_admin": User.objects.create_user(  # nosec: B106
            username="workspace_admin",
            email="workspace_admin@example.com",
            # password="password-workspace-admin",
            name="workspace admin",
        ),
        "workspace_member": User.objects.create_user(  # nosec: B106
            username="workspace_member",
            email="user@example.com",
            password="password-user",
            name="user",
        ),
    }


@pytest.fixture()
def test_workspaces(db) -> dict:
    return {
        "workspace_private": Workspace.objects.create(
            name="test workspace",
            visibility="PRIVATE",
        ),
        "workspace_public": Workspace.objects.create(
            name="test workspace public",
            visibility="PUBLIC",
        ),
    }


@pytest.fixture()
def test_memberships(db, test_users, test_workspaces) -> dict:
    return {
        "workspace_private_admin": Membership.objects.create(
            user=test_users.get("workspace_admin"),
            object_uuid=test_workspaces.get("workspace_private").uuid,
            object_type=MSP_WORKSPACE,
            role=WS_ADMIN,
        ),
        "workspace_private_member": Membership.objects.create(
            user=test_users.get("workspace_member"),
            object_uuid=test_workspaces.get("workspace_private").uuid,
            object_type=MSP_WORKSPACE,
            role=WS_MEMBER,
        ),
    }


@pytest.fixture()
def test_projects(db, test_workspaces) -> dict:
    return {
        "project_private": Project.objects.create(
            name="test project",
            workspace=test_workspaces.get("workspace_private"),
            visibility="PRIVATE",
        ),
        "project_public": Project.objects.create(
            name="test project public",
            workspace=test_workspaces.get("workspace_public"),
            visibility="PUBLIC",
        ),
    }


@pytest.fixture()
def test_jobs(db, test_projects) -> dict:
    return {
        "job_private": JobDef.objects.create(
            name="test job",
            project=test_projects.get("project_private"),
        ),
        "job_public": JobDef.objects.create(
            name="test job public",
            project=test_projects.get("project_public"),
        ),
    }
