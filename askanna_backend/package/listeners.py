import os
from zipfile import ZipFile

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver

from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from job.models import JobDef
from package.signals import package_upload_finish


@receiver(package_upload_finish)
def handle_upload(sender, signal, postheaders, obj, **kwargs):
    # extract from package_root to blob_root under the package uuid
    # this is for the fileview
    source_location = settings.PACKAGES_ROOT
    target_location = settings.BLOB_ROOT

    source_path = os.path.join(source_location, obj.storage_location)
    target_path = os.path.join(target_location, str(obj.uuid))

    with ZipFile(source_path) as zippackage:
        zippackage.extractall(path=target_path)


@receiver(package_upload_finish)
def extract_jobs_from_askannayml(sender, signal, postheaders, obj, **kwargs):
    """
    Extract jobs defined in the askanna.yml (if set)
    """
    source_location = settings.PACKAGES_ROOT
    source_path = os.path.join(source_location, obj.storage_location)

    # Read the zipfile and find askanna.yml
    askanna_yml = ""
    with ZipFile(source_path) as zipObj:
        listOfFileNames = zipObj.namelist()

        askanna_ymlfiles = set(["askanna.yml", "askanna.yaml"])
        found_askanna_yml = askanna_ymlfiles - (askanna_ymlfiles - set(listOfFileNames))
        yml_found_in_set = len(found_askanna_yml) < len(askanna_ymlfiles)

        if not yml_found_in_set:
            return

        askanna_yml = zipObj.read(list(found_askanna_yml)[0])

    config = load(askanna_yml, Loader=Loader)

    # Within AskAnna, we have several variables reserved
    reserved_keys = (
        "cluster",
        "environment",
        "push-target",
        "variables",
    )
    project = obj.project

    jobs = list(set(config.keys()) - set(reserved_keys))

    # create or find jobdef for each found jobs

    for job in jobs:
        try:
            jd = JobDef.objects.get(name=job, project=project)
        except ObjectDoesNotExist as e:
            jd = JobDef.objects.create(name=job, project=project, owner=obj.created_by)

