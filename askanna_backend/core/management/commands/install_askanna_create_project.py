# -*- coding: utf-8 -*-
import os
import tempfile
import uuid
import warnings
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from job.models import JobDef
from package.models import Package
from project.models import Project
from workspace.models import Workspace


def package(src: str) -> str:
    pwd_dir_name = os.path.basename(src)
    random_suffix = uuid.uuid4().hex

    tmpdir = tempfile.mkdtemp(prefix="askanna-package")
    random_file_name = os.path.join(tmpdir, f"{pwd_dir_name}_{random_suffix}.zip")

    zip_files_in_dir(src, random_file_name, lambda x: x)
    return random_file_name


# Zip the files from given directory that matches the filter
def zip_files_in_dir(dir_name: str, zip_file_name: str, filter):
    os.chdir(dir_name)
    # Create a ZipFile object
    with ZipFile(zip_file_name, mode="w") as zip_file:
        # Iterate over all the files in directory
        for folder_name, _, filenames in os.walk("."):
            for filename in filenames:
                if filter(filename):
                    # Create complete filepath of file in directory
                    filePath = os.path.join(folder_name, filename)
                    # Add file to zip
                    zip_file.write(filePath)


class Command(BaseCommand):
    help = "Install 'AskAnna Create Project' in workspace 'AskAnna Core'"

    def handle(self, *args, **options):
        # Make sure we are operating on the 'AskAnna workspace'
        workspace, workspace_created = Workspace.objects.get_or_create(
            uuid="695fcc8b-ba8c-4575-a1e0-f0fcfc70a349",
            short_uuid="3Cpy-QMzd-MVko-1rDQ",
        )
        if workspace_created:
            workspace.name = "AskAnna Core"
            workspace.visibility = "PRIVATE"
            workspace.save()
        elif workspace.name != "AskAnna Core" or workspace.visibility != "PRIVATE":
            warnings.warn(
                "Workspace '3Cpy-QMzd-MVko-1rDQ' already exists but is not configured with the expected workspace "
                "name or workspace visibility."
            )

        # Make sure we operate on the 'AskAnna Create Project' project
        project, project_created = Project.objects.get_or_create(
            uuid=uuid.UUID("f1823c3b-e9e7-47bb-a610-5462c9cd9767"),
            short_uuid="7Lif-Rhcn-IRvS-Wv7J",
            workspace=workspace,
        )
        if project_created:
            project.name = "AskAnna Create Project"
            project.visibility = "PRIVATE"
            project.save()
        elif project.name != "AskAnna Create Project" or project.visibility != "PRIVATE":
            raise Warning(
                "Project '7Lif-Rhcn-IRvS-Wv7J' already exists but is not configured with the expected project name "
                "or project visibility."
            )

        # Make sure the job is available for triggering 'create_project'
        jobdef, job_created = JobDef.objects.get_or_create(
            uuid=uuid.UUID("c744a283-f307-40e1-a21d-570bbbe6d9d2"),
            short_uuid="640q-2AMP-T5BL-Cnml",
        )
        if job_created:
            jobdef.name = "create_project"
            jobdef.project = project
            jobdef.save()
        elif jobdef.name != "create_project" or jobdef.project != project:
            raise Warning(
                "Job '640q-2AMP-T5BL-Cnml' already exists but is not configured with the expected job name or project."
            )

        # Create the package for the project
        # use from our `resources/projects/askanna_create_project` folder
        # TODO: on every deployment, we should only create the package when a new version is available
        package_archive = package(settings.ROOT_DIR.path("resources/projects/askanna_create_project"))
        package_object = Package.objects.create(
            original_filename="askanna_create_project.zip",
            project=project,
            size=os.stat(package_archive).st_size,
            finished=timezone.now(),
        )
        package_object.write(open(package_archive, "rb"))
