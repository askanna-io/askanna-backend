# import io
# import json
# import os
# import sys

# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# from job.models import JobDef, JobPayload, JobRun
# from package.models import Package
from workspace.models import Workspace
from users.models import (
    # User,
    Membership,
)


@receiver(post_delete, sender=Workspace)
def remove_memberships_after_workspace_removal(sender, instance, **kwargs):
    """
    Memberships don't have a hard link, so remove manually
    """
    members_in_workspace = Membership.objects.filter(
        object_type="WS", object_uuid=instance.uuid
    )
    for member in members_in_workspace:
        member.delete()


@receiver(post_save, sender=Workspace)
def install_demo_project_in_workspace(sender, instance, **kwargs):
    # this code is disabled untill the `askanna run` is finished`
    pass
    # workspace = instance
    # workspace_suuid = workspace.short_uuid

    # trigger celery job with the following args:
    # workspace_suuid
    # job to trigger= settings.JOB_CREATE_PROJECT_SUUID

    # anna = User.objects.get(pk=1)

    # jobdef = JobDef.objects.get(short_uuid=settings.JOB_CREATE_PROJECT_SUUID)
    # json_string = json.dumps({"WORKSPACE_SUUID": workspace_suuid,})
    # job_pl = JobPayload.objects.create(
    #     jobdef=jobdef, size=len(json_string), lines=3, owner=anna
    # )
    # job_pl.write(io.StringIO(json_string))

    # # FIXME: Determine wheter we need the latest or pinned package
    # # Fetch the latest package found in the jobdef.project
    # package = (
    #     Package.objects.filter(finished__isnull=False).filter(project=jobdef.project).order_by("-created").first()
    # )

    # # create new Jobrun
    # jobrun = JobRun.objects.create(
    #     status="PENDING", jobdef=jobdef, payload=job_pl, package=package, owner=anna,
    # )
