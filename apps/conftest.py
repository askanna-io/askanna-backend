import pytest

from account.models.membership import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership
from account.models.user import User
from job.models import JobDef
from project.models import Project
from tests.utils import get_avatar_content_file
from variable.models import Variable
from workspace.models import Workspace


@pytest.fixture()
def test_users(db):
    users = {
        "askanna_super_admin": User.objects.create_superuser(  # nosec: B106  # type: ignore
            username="askanna_super_admin@dev.com",
            is_staff=True,
            is_superuser=True,
            email="askanna_super_admin@dev.com",
            password="password-admin",
            name="admin",
        ),
        "workspace_admin": User.objects.create_user(  # type: ignore
            username="workspace_admin@dev.com",
            email="workspace_admin@dev.com",
            name="workspace admin",
        ),
        "workspace_member": User.objects.create_user(  # nosec: B106  # type: ignore
            username="workspace_member@dev.com",
            email="workspace_member@dev.com",
            password="password-user",
            name="workspace member",
        ),
        "no_workspace_member": User.objects.create_user(  # type: ignore
            username="no_workspace_member@dev.com",
            email="no_workspace_member@dev.com",
            name="no workspace member",
        ),
    }

    yield users

    for user in users.values():
        user.delete_avatar_files()
        user.delete()


@pytest.fixture()
def test_avatar_files(test_users):
    test_users["workspace_admin"].set_avatar(get_avatar_content_file())

    avatar_files = {
        "workspace_admin": test_users["workspace_admin"].avatar_files,
    }

    yield avatar_files

    for avatar_file in avatar_files.keys():
        test_users[avatar_file].delete_avatar_files()


@pytest.fixture()
def test_workspaces(test_users):
    workspaces = {
        "workspace_private": Workspace.objects.create(
            name="test workspace private",
            visibility="PRIVATE",
            created_by_user=test_users["workspace_admin"],
        ),
        "workspace_public": Workspace.objects.create(
            name="test workspace public",
            visibility="PUBLIC",
            created_by_user=test_users["workspace_admin"],
        ),
    }

    yield workspaces

    for workspace in workspaces.values():
        workspace.delete()


@pytest.fixture()
def test_memberships(test_users, test_workspaces):
    workspace_private_admin = Membership.objects.get(
        user=test_users["workspace_admin"],
        object_uuid=test_workspaces["workspace_private"].uuid,
        object_type=MSP_WORKSPACE,
        role=WS_ADMIN,
    )
    workspace_public_admin = Membership.objects.get(
        user=test_users["workspace_admin"],
        object_uuid=test_workspaces["workspace_public"].uuid,
        object_type=MSP_WORKSPACE,
        role=WS_ADMIN,
    )

    workspace_private_admin.name = "workspace private admin"  # type: ignore
    workspace_private_admin.job_title = "job_title of workspace private admin"  # type: ignore
    workspace_private_admin.use_global_profile = True
    workspace_private_admin.save()

    memberships = {
        "workspace_private_admin": workspace_private_admin,
        "workspace_private_member": Membership.objects.create(
            user=test_users["workspace_member"],
            name="workspace private member",
            job_title="job_title of workspace private member",
            use_global_profile=False,
            object_uuid=test_workspaces["workspace_private"].uuid,
            object_type=MSP_WORKSPACE,
            role=WS_MEMBER,
        ),
        "workspace_public_admin": workspace_public_admin,
    }

    yield memberships

    for membership in memberships.values():
        membership.delete_avatar_files()
        membership.delete()


@pytest.fixture()
def test_projects(test_workspaces):
    projects = {
        "project_private": Project.objects.create(
            name="test project private",
            visibility="PRIVATE",
            workspace=test_workspaces["workspace_private"],
        ),
        "project_public": Project.objects.create(
            name="test project public",
            visibility="PUBLIC",
            workspace=test_workspaces["workspace_public"],
        ),
    }

    yield projects

    for project in projects.values():
        project.delete()


@pytest.fixture()
def test_variables(test_projects):
    variables = {
        "variable_private": Variable.objects.create(
            name="test variable private",
            value="test variable private value",
            project=test_projects["project_private"],
        ),
        "variable_private_masked": Variable.objects.create(
            name="test variable private masked",
            value="test variable private masked value",
            is_masked=True,
            project=test_projects["project_private"],
        ),
        "variable_public": Variable.objects.create(
            name="test variable public",
            value="test variable public value",
            project=test_projects["project_public"],
        ),
        "variable_public_masked": Variable.objects.create(
            name="test variable public masked",
            value="test variable public masked value",
            is_masked=True,
            project=test_projects["project_public"],
        ),
    }

    yield variables

    for variable in variables.values():
        variable.delete()


@pytest.fixture()
def test_jobs(db, test_projects):
    jobs = {
        "job_private": JobDef.objects.create(
            name="test job",
            project=test_projects.get("project_private"),
        ),
        "job_public": JobDef.objects.create(
            name="test job public",
            project=test_projects.get("project_public"),
        ),
    }

    yield jobs

    for job in jobs.values():
        job.delete()
