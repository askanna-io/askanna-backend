import os
import tempfile
import uuid
import warnings
from pathlib import Path
from zipfile import ZipFile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from account.models import User
from job.models import JobDef
from package.models import Package
from project.models import Project
from workspace.models import Workspace


def package(source: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="askanna-package"))
    zip_file_path = temp_dir / f"{source.name}_{uuid.uuid4().hex}.zip"

    with ZipFile(zip_file_path, mode="w") as zip_file:
        for directory, _, files in os.walk(source):
            if directory == str(source):
                archive_directory = ""
            else:
                archive_directory = directory.replace(str(source) + "/", "")
                # Always add the directory to the zip file to make sure we also include empty directories
                zip_file.write(Path(directory), Path(archive_directory))

            for file in files:
                zip_file.write(
                    filename=Path(directory) / file,
                    arcname=Path(archive_directory) / file,
                )

    return zip_file_path


class Command(BaseCommand):
    help = "Install 'AskAnna Create Project' in workspace 'AskAnna Core'"

    def handle(self, *args, **options):
        user_anna, _ = User.objects.get_or_create(username="anna")

        # Make sure we are operating on the 'AskAnna workspace'
        workspace_uuid = uuid.UUID("695fcc8b-ba8c-4575-a1e0-f0fcfc70a349")
        workspace_suuid = "3Cpy-QMzd-MVko-1rDQ"
        workspace_name = "AskAnna Core"
        workspace_visibility = "PRIVATE"
        try:
            workspace = Workspace.objects.get(
                uuid=workspace_uuid,
                suuid=workspace_suuid,
            )
        except Workspace.DoesNotExist:
            workspace = Workspace.objects.create(
                uuid=workspace_uuid,
                suuid=workspace_suuid,
                name=workspace_name,
                visibility=workspace_visibility,
                created_by=user_anna,
            )

        if workspace.name != workspace_name or workspace.visibility != workspace_visibility:
            warnings.warn(
                "Workspace '3Cpy-QMzd-MVko-1rDQ' exists but is not configured with the expected workspace name or "
                "workspace visibility.",
                category=Warning,
                stacklevel=1,
            )

        # Make sure we operate on the 'AskAnna Create Project' project
        project_uuid = uuid.UUID("f1823c3b-e9e7-47bb-a610-5462c9cd9767")
        project_suuid = "7Lif-Rhcn-IRvS-Wv7J"
        project_name = "AskAnna Create Project"
        project_visibility = "PRIVATE"
        try:
            project = Project.objects.get(
                uuid=project_uuid,
                suuid=project_suuid,
                workspace=workspace,
            )
        except Project.DoesNotExist:
            project = Project.objects.create(
                uuid=project_uuid,
                suuid=project_suuid,
                name=project_name,
                visibility=project_visibility,
                workspace=workspace,
                created_by=user_anna,
            )

        if project.name != project_name or project.visibility != project_visibility:
            warnings.warn(
                "Project '7Lif-Rhcn-IRvS-Wv7J' exists but is not configured with the expected project name or "
                "project visibility.",
                category=Warning,
                stacklevel=1,
            )

        # Make sure the job is available for triggering 'create_project'
        jobdef, job_created = JobDef.objects.get_or_create(
            uuid=uuid.UUID("c744a283-f307-40e1-a21d-570bbbe6d9d2"),
            suuid="640q-2AMP-T5BL-Cnml",
        )
        if job_created:
            jobdef.name = "create_project"
            jobdef.project = project
            jobdef.save()
        elif jobdef.name != "create_project" or jobdef.project != project:
            warnings.warn(
                "Job '640q-2AMP-T5BL-Cnml' already exists but is not configured with the expected job name or "
                "project.",
                category=Warning,
                stacklevel=1,
            )

        # Create the package for the project use from our `resources/projects/askanna_create_project` directory
        dir_to_pack = settings.BASE_DIR / "resources/projects/askanna_create_project"
        package_archive = package(source=dir_to_pack)

        latest_package = Package.objects.filter(project=project).order_by("-created_at").first()
        if latest_package and package_archive.stat().st_size == latest_package.size:
            # The package is already available, no need to create a new one
            return

        package_object = Package.objects.create(
            original_filename="askanna_create_project.zip",
            project=project,
            size=package_archive.stat().st_size,
            finished_at=timezone.now(),
            created_by=user_anna,
        )
        package_object.write(package_archive.open("rb"))
