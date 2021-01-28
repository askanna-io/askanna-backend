import json
import os
import tempfile
import uuid
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.conf import settings

from job.models import JobDef
from package.models import Package
from project.models import Project
from workspace.models import Workspace


def package(src: str) -> str:

    pwd_dir_name = os.path.basename(src)
    random_suffix = uuid.uuid4().hex

    # make a temporary directory
    tmpdir = tempfile.mkdtemp(prefix="askanna-package")

    random_name = os.path.join(
        tmpdir,
        "{pwd_dir_name}_{random_suffix}.zip".format(
            pwd_dir_name=pwd_dir_name, random_suffix=random_suffix
        ),
    )

    zipFilesInDir(src, random_name, lambda x: x)
    return random_name


# Zip the files from given directory that matches the filter
def zipFilesInDir(dirName, zipFileName, filter):
    os.chdir(dirName)
    # create a ZipFile object
    with ZipFile(zipFileName, mode="w") as zipObj:
        # Iterate over all the files in directory
        for folderName, subfolders, filenames in os.walk("."):
            for filename in filenames:
                if filter(filename):
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # Add file to zip
                    zipObj.write(filePath)


class Command(BaseCommand):
    help = "Install initial fixtures for askanna create project"

    def handle(self, *args, **options):
        # make sure we are operating on the AskAnna workspace
        workspace, _created = Workspace.objects.get_or_create(
            uuid="695fcc8b-ba8c-4575-a1e0-f0fcfc70a349",
            short_uuid="3Cpy-QMzd-MVko-1rDQ",
        )

        # make sure we operate on the "create project" project
        project, _created = Project.objects.get_or_create(
            uuid=uuid.UUID("f1823c3b-e9e7-47bb-a610-5462c9cd9767"),
            short_uuid="7Lif-Rhcn-IRvS-Wv7J",
            workspace=workspace,
        )
        project.name = "AskAnna Core"
        project.save()

        # also make the job available for triggering "create project"
        jobdef, _created = JobDef.objects.get_or_create(
            uuid=uuid.UUID("c744a283-f307-40e1-a21d-570bbbe6d9d2"),
            short_uuid="640q-2AMP-T5BL-Cnml",
        )
        jobdef.name = "createproject"
        jobdef.project = project
        jobdef.save()

        # create the package for the project
        # use from our `resources/projects/askanna_core` folder

        package_archive = package(
            settings.ROOT_DIR.path("resources/projects/askanna_core")
        )

        # register package
        pkg = Package.objects.create(
            original_filename="askanna_core.zip",
            project=project,
            size=os.stat(package_archive).st_size,
        )
        pkg.write(open(package_archive, "rb"))
