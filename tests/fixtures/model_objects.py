import io
import json
from datetime import datetime
from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from account.models.membership import MSP_WORKSPACE, Membership
from account.models.user import User
from core.models.object_reference import ObjectReference
from core.permissions.roles import WorkspaceAdmin, WorkspaceMember, WorkspaceViewer
from job.models import JobDef
from package.models import Package
from project.models import Project
from run.models import Run, RunArtifact, RunMetric, RunVariable
from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file
from variable.models import Variable
from workspace.models import Workspace


@pytest.fixture()
def test_users(db) -> dict[str, User]:
    users = {
        "askanna_super_admin": User.objects.create_superuser(  # nosec: B106
            username="askanna_super_admin@dev.com",
            is_staff=True,
            is_superuser=True,
            email="askanna_super_admin@dev.com",
            password="password-admin",
            name="admin",
        ),
        "workspace_admin": User.objects.create_user(
            username="workspace_admin@dev.com",
            email="workspace_admin@dev.com",
            name="workspace admin",
        ),
        "workspace_admin_2": User.objects.create_user(
            username="workspace_admin_2@dev.com",
            email="workspace_admin_2@dev.com",
            name="workspace admin 2",
        ),
        "workspace_member": User.objects.create_user(  # nosec: B106
            username="workspace_member@dev.com",
            email="workspace_member@dev.com",
            password="password-user",
            name="workspace member",
        ),
        "workspace_viewer": User.objects.create_user(
            username="workspace_viewer@dev.com",
            email="workspace_viewer@dev.com",
            name="workspace viewer",
        ),
        "no_workspace_member": User.objects.create_user(
            username="no_workspace_member@dev.com",
            email="no_workspace_member@dev.com",
            name="no workspace member",
        ),
        "inactive_member": User.objects.create_user(
            username="not_active@dev.com",
            email="not_active@dev.com",
            name="not active member",
            is_active=False,
        ),
    }

    yield users

    for user in users.values():
        user.delete()


@pytest.fixture()
def test_avatar_files(test_users, avatar_content_file):  # noqa: F811
    test_users["workspace_admin"].set_avatar(avatar_content_file)

    avatar_files = {
        "workspace_admin": test_users["workspace_admin"].avatar_file,
    }

    yield avatar_files

    for avatar_file in avatar_files.keys():
        test_users[avatar_file].delete_avatar_file()


@pytest.fixture()
def test_workspaces(test_users) -> dict[str, Workspace]:
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
        "workspace_private_admin_2": Workspace.objects.create(
            name="test workspace private with another admin",
            visibility="PRIVATE",
            created_by_user=test_users["workspace_admin_2"],
        ),
    }

    yield workspaces

    for workspace in workspaces.values():
        workspace.delete()


@pytest.fixture()
def test_memberships(test_users, test_workspaces) -> dict[str, Membership]:
    workspace_private_admin = Membership.objects.get(
        user=test_users["workspace_admin"],
        object_uuid=test_workspaces["workspace_private"].uuid,
        object_type=MSP_WORKSPACE,
        role=WorkspaceAdmin.code,
    )
    workspace_public_admin = Membership.objects.get(
        user=test_users["workspace_admin"],
        object_uuid=test_workspaces["workspace_public"].uuid,
        object_type=MSP_WORKSPACE,
        role=WorkspaceAdmin.code,
    )

    workspace_private_admin.name = "workspace private admin"
    workspace_private_admin.job_title = "job_title of workspace private admin"
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
            role=WorkspaceMember.code,
        ),
        "workspace_private_viewer": Membership.objects.create(
            user=test_users["workspace_viewer"],
            name="workspace private viewer",
            job_title="job_title of workspace private viewer",
            use_global_profile=False,
            object_uuid=test_workspaces["workspace_private"].uuid,
            object_type=MSP_WORKSPACE,
            role=WorkspaceViewer.code,
        ),
        "workspace_public_admin": workspace_public_admin,
    }

    yield memberships

    for membership in memberships.values():
        membership.delete()


@pytest.fixture()
def test_projects(test_workspaces) -> dict[str, Project]:
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
        "project_private_admin_2": Project.objects.create(
            name="test project private with another admin",
            visibility="PRIVATE",
            workspace=test_workspaces["workspace_private_admin_2"],
        ),
    }

    yield projects

    for project in projects.values():
        project.delete()


@pytest.fixture()
def test_variables(test_projects) -> dict[str, Variable]:
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
def test_packages(test_projects, test_memberships) -> dict[str, Package]:
    packages = {
        "package_private_1": Package.objects.create(
            project=test_projects["project_private"],
        ),
        "package_private_2": Package.objects.create(
            project=test_projects["project_private"],
        ),
        "package_private_3": Package.objects.create(
            project=test_projects["project_private"],
        ),
        "package_private_4": Package.objects.create(
            project=test_projects["project_private"],
        ),
        "package_public": Package.objects.create(
            project=test_projects["project_public"],
        ),
    }

    file_project_with_config = ContentFile(
        content=Path(settings.TEST_RESOURCES_DIR / "projects" / "project-001.zip").read_bytes(),
        name="project_with_config.zip",
    )

    packages["package_private_1"].package_file = File.objects.create(
        name=file_project_with_config.name,
        file=file_project_with_config,
        size=file_project_with_config.size,
        etag=get_md5_from_file(file_project_with_config),
        content_type=get_content_type_from_file(file_project_with_config),
        completed_at=timezone.now(),
        created_for=packages["package_private_1"],
        created_by=test_memberships["workspace_private_admin"],
    )
    packages["package_private_1"].save()

    packages["package_private_2"].package_file = File.objects.create(
        name="mixed_format_archive.zip",
        created_for=packages["package_private_2"],
        created_by=test_memberships["workspace_private_admin"],
    )
    packages["package_private_2"].save()

    packages["package_private_3"].package_file = File.objects.create(
        name=file_project_with_config.name,
        file=file_project_with_config,
        size=file_project_with_config.size,
        etag=get_md5_from_file(file_project_with_config),
        content_type=get_content_type_from_file(file_project_with_config),
        completed_at=timezone.now(),
        created_for=packages["package_private_3"],
        created_by=test_memberships["workspace_private_member"],
    )
    packages["package_private_3"].save()

    packages["package_public"].package_file = File.objects.create(
        name=file_project_with_config.name,
        file=file_project_with_config,
        size=file_project_with_config.size,
        etag=get_md5_from_file(file_project_with_config),
        content_type=get_content_type_from_file(file_project_with_config),
        completed_at=timezone.now(),
        created_for=packages["package_public"],
        created_by=test_memberships["workspace_private_admin"],
    )
    packages["package_public"].save()

    yield packages

    for package in packages.values():
        package.delete()


@pytest.fixture()
def test_storage_files(test_packages) -> dict[str, File]:
    return {
        "file_private_project_with_config": test_packages["package_private_1"].package_file,
        "file_private_not_completed": test_packages["package_private_2"].package_file,
        "file_private_project_package_3": test_packages["package_private_3"].package_file,
        "file_public_project_package_public": test_packages["package_public"].package_file,
    }


@pytest.fixture()
def test_jobs(test_projects) -> dict[str, JobDef]:
    jobs = {
        "job_private": JobDef.objects.create(
            name="test job",
            project=test_projects.get("project_private"),
        ),
        "my-test-job": JobDef.objects.create(
            name="my-test-job",
            project=test_projects.get("project_private"),
        ),
        "job_public": JobDef.objects.create(
            name="test job public",
            project=test_projects.get("project_public"),
        ),
        "job_private_admin_2": JobDef.objects.create(
            name="test job private with another admin",
            project=test_projects.get("project_private_admin_2"),
        ),
    }

    yield jobs

    for job in jobs.values():
        job.delete()


@pytest.fixture()
def test_runs(
    test_jobs,
    test_packages,
    test_storage_files,
    test_memberships,
) -> dict[str, Run]:
    runs = {
        "run_1": Run.objects.create(
            name="test run 1",
            jobdef=test_jobs["my-test-job"],
            package=test_packages["package_private_1"],
            created_by_user=test_memberships["workspace_private_admin"].user,
            created_by_member=test_memberships["workspace_private_admin"],
        ),
        "run_2": Run.objects.create(
            name="",  # test run 2 without a name set
            jobdef=test_jobs["my-test-job"],
            status="COMPLETED",
            started_at=timezone.now() - timezone.timedelta(seconds=30),
            finished_at=timezone.now() + timezone.timedelta(seconds=30),
            package=test_packages["package_private_1"],
            created_by_user=test_memberships["workspace_private_member"].user,
            created_by_member=test_memberships["workspace_private_member"],
        ),
        "run_3": Run.objects.create(
            name="test run 3 failed",
            jobdef=test_jobs["job_private"],
            package=test_packages["package_private_1"],
            status="FAILED",
            started_at=timezone.now(),
            finished_at=timezone.now() + timezone.timedelta(seconds=30),
            created_by_user=test_memberships["workspace_private_admin"].user,
            created_by_member=test_memberships["workspace_private_admin"],
            trigger="WEBUI",
        ),
        "run_4": Run.objects.create(
            name="test run 4 public",
            jobdef=test_jobs["job_public"],
            package=test_packages["package_public"],
            status="IN_PROGRESS",
            started_at=timezone.now(),
            created_by_user=test_memberships["workspace_public_admin"].user,
            created_by_member=test_memberships["workspace_public_admin"],
            trigger="CLI",
        ),
        "run_5": Run.objects.create(
            name="test run 5 failed",
            jobdef=test_jobs["job_private"],
            package=test_packages["package_private_4"],
            status="FAILED",
            started_at=timezone.now(),
            finished_at=timezone.now() + timezone.timedelta(seconds=30),
            created_by_user=test_memberships["workspace_private_admin"].user,
            created_by_member=test_memberships["workspace_private_admin"],
        ),
    }

    log_content_file = ContentFile(
        content=io.BytesIO(
            json.dumps(
                [
                    [1, datetime.utcnow().isoformat(), "some test stdout 1"],
                    [2, datetime.utcnow().isoformat(), "some test stdout 2"],
                    [3, datetime.utcnow().isoformat(), "some test stdout 3"],
                    [3, datetime.utcnow().isoformat(), "some test stdout 4"],
                    [5, datetime.utcnow().isoformat(), "some test stdout 5"],
                    [6, datetime.utcnow().isoformat(), "some test stdout 6"],
                ]
            ).encode()
        ).read(),
        name="log.json",
    )
    runs["run_2"].log_file = File.objects.create(
        name=log_content_file.name,
        file=log_content_file,
        size=log_content_file.size,
        etag=get_md5_from_file(log_content_file),
        content_type=get_content_type_from_file(log_content_file),
        completed_at=timezone.now(),
        created_for=runs["run_2"],
        created_by=runs["run_2"].created_by_member,
    )

    result_content_file = ContentFile(
        content=io.BytesIO(b"some private result content").read(),
        name="result_private.txt",
    )
    runs["run_2"].result_file = File.objects.create(
        name=result_content_file.name,
        file=result_content_file,
        size=result_content_file.size,
        etag=get_md5_from_file(result_content_file),
        content_type=get_content_type_from_file(result_content_file),
        completed_at=timezone.now(),
        created_for=runs["run_2"],
        created_by=runs["run_2"].created_by_member,
    )
    payload_file_path = settings.TEST_RESOURCES_DIR / "payloads/test-payload.json"
    payload_content_file = ContentFile(
        content=payload_file_path.read_bytes(),
        name="payload.json",
    )
    runs["run_2"].payload_file = File.objects.create(
        name=payload_content_file.name,
        file=payload_content_file,
        size=payload_content_file.size,
        etag=get_md5_from_file(payload_content_file),
        content_type=get_content_type_from_file(payload_content_file),
        completed_at=timezone.now(),
        created_for=runs["run_2"],
        created_by=runs["run_2"].created_by_member,
    )
    runs["run_2"].save()

    result_content_file = ContentFile(
        content=io.BytesIO(b"some public result content").read(),
        name="result_public.txt",
    )
    runs["run_4"].result_file = File.objects.create(
        name=result_content_file.name,
        file=result_content_file,
        size=result_content_file.size,
        etag=get_md5_from_file(result_content_file),
        content_type=get_content_type_from_file(result_content_file),
        completed_at=timezone.now(),
        created_for=runs["run_4"],
        created_by=runs["run_4"].created_by_member,
    )
    payload_file_path = settings.TEST_RESOURCES_DIR / "payloads/test-payload.json"
    payload_content_file = ContentFile(
        content=payload_file_path.read_bytes(),
        name="payload.json",
    )
    runs["run_4"].payload_file = File.objects.create(
        name=payload_content_file.name,
        file=payload_content_file,
        size=payload_content_file.size,
        etag=get_md5_from_file(payload_content_file),
        content_type=get_content_type_from_file(payload_content_file),
        completed_at=timezone.now(),
        created_for=runs["run_4"],
        created_by=runs["run_4"].created_by_member,
    )
    runs["run_4"].save()

    yield runs

    for run in runs.values():
        run.delete()


@pytest.fixture()
def test_run_artifacts(test_runs, test_memberships) -> dict[str, RunArtifact]:
    artifacts = {
        "artifact_1": RunArtifact.objects.create(run=test_runs["run_1"]),
    }

    ObjectReference.objects.create(run_artifact=artifacts["artifact_1"])

    artifact_1_content_file = ContentFile(
        content=Path(settings.TEST_RESOURCES_DIR / "artifacts" / "artifact-aa.zip").read_bytes(),
        name="artifact-aa.zip",
    )

    artifacts["artifact_1"].artifact_file = File.objects.create(
        name=artifact_1_content_file.name,
        file=artifact_1_content_file,
        size=artifact_1_content_file.size,
        etag=get_md5_from_file(artifact_1_content_file),
        content_type=get_content_type_from_file(artifact_1_content_file),
        completed_at=timezone.now(),
        created_for=artifacts["artifact_1"],
        created_by=test_memberships["workspace_private_admin"],
    )
    artifacts["artifact_1"].save()

    yield artifacts

    for artifact in artifacts.values():
        artifact.delete()


@pytest.fixture()
def test_run_metrics(test_runs, create_metric_dict, create_metric_dict_small_no_label) -> None:
    run_metric_objects = []
    metrics = create_metric_dict(test_runs["run_2"].suuid)
    for metric in metrics:
        run_metric_objects.append(
            RunMetric.objects.create(
                run=test_runs["run_2"],
                metric=metric["metric"],
                label=metric["label"],
                created_at=metric["created_at"],
            )
        )

    metrics = create_metric_dict_small_no_label(test_runs["run_4"].suuid)
    for metric in metrics:
        run_metric_objects.append(
            RunMetric.objects.create(
                run=test_runs["run_4"],
                metric=metric["metric"],
                label=metric["label"],
                created_at=metric["created_at"],
            )
        )

    yield

    for run_metric_object in run_metric_objects:
        run_metric_object.delete()


@pytest.fixture()
def test_run_variables(test_runs, create_variable_dict, create_variable_dict_small_no_label) -> None:
    run_variable_objects = []
    variables = create_variable_dict(test_runs["run_2"].suuid)
    for variable in variables:
        run_variable_objects.append(
            RunVariable.objects.create(
                run=test_runs["run_2"],
                variable=variable["variable"],
                label=variable["label"],
                created_at=variable["created_at"],
            )
        )

    variables = create_variable_dict_small_no_label(test_runs["run_4"].suuid)
    for variable in variables:
        run_variable_objects.append(
            RunVariable.objects.create(
                run=test_runs["run_4"],
                variable=variable["variable"],
                label=variable["label"],
                created_at=variable["created_at"],
            )
        )

    yield

    for run_variable_object in run_variable_objects:
        run_variable_object.delete()
