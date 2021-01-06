import os
from zipfile import ZipFile

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_delete, post_delete, pre_save
from django.dispatch import receiver
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from job.models import JobDef
from package.models import Package
from package.signals import package_upload_finish
from users.models import MSP_WORKSPACE


@receiver(package_upload_finish)
def handle_upload(sender, signal, postheaders, obj, **kwargs):
    # extract from package_root to blob_root under the package uuid
    # this is for the fileview
    target_location = settings.BLOB_ROOT

    source_path = obj.stored_path
    target_path = os.path.join(target_location, str(obj.uuid))

    with ZipFile(source_path) as zippackage:
        zippackage.extractall(path=target_path)


@receiver(package_upload_finish)
def extract_jobs_from_askannayml(sender, signal, postheaders, obj, **kwargs):
    """
    Extract jobs defined in the askanna.yml (if set)

    The `askanna.yml` file should be located in the root level of the archive
    """
    source_path = obj.stored_path

    # Read the zipfile and find askanna.yml
    askanna_yml = ""
    with ZipFile(source_path) as zipObj:
        listOfFileNames = zipObj.namelist()

        askanna_ymlfiles = set(["askanna.yml", "askanna.yaml"])
        found_askanna_yml = askanna_ymlfiles - (askanna_ymlfiles - set(listOfFileNames))
        yml_found_in_set = len(found_askanna_yml) > 0

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


@receiver(pre_delete, sender=Package)
def delete_package(sender, instance, **kwargs):
    instance.prune()


@receiver(pre_save, sender=Package)
def add_member_to_package(sender, instance, **kwargs):
    """
    On update of a package, add the member to it who created this.
    We already thave the user, but we lookup the membership for it
    (we know this by project->workspace)
    We only know the instance.created_by when an upload was finished
    So this signal is executed twice, but we only update when the
    created_by is filled
    """
    if (not instance.member) and instance.created_by:
        # first lookup which member this could be based on workspace
        in_workspace = instance.project.workspace
        member_query = instance.created_by.memberships.filter(
            object_uuid=in_workspace.uuid,
            object_type=MSP_WORKSPACE,
            deleted__isnull=True,
        )
        if member_query.exists():
            # get the membership out of it
            membership = member_query.first()
            if membership:
                instance.member = membership

