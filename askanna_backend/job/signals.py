import os
import sys

from celery import shared_task

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string
from django.db.transaction import on_commit

from job.models import (
    JobDef,
    JobRun,
    JobPayload,
    JobOutput,
)

from package.models import Package

@shared_task(bind=True)
def start_jobrun(self, jobrun_uuid):
    print(f"Received message to start jobrun {jobrun_uuid}")

    # First save current Celery id to the jobid field
    jr = JobRun.objects.get(pk=jobrun_uuid)
    jr.jobid = self.request.id
    jr.status = 'PENDING'
    jr.save(update_fields=['jobid', 'status'])

    # What is the jobdef specified?
    jd = jr.jobdef
    pl = jr.payload

    # FIXME: when versioning is in, point to version in JobRun
    package = Package.objects.filter(project=jd.project).last()

    # compose the path to the package in the project
    # This points to the blob location where the package is
    package_path = os.path.join( settings.BLOB_ROOT, str(package.uuid) )
    # Add this to the python path for this session, to resolve to the package code
    sys.path.insert(0, package_path)

    sys_modules_before = list(sys.modules)

    try:
        print("*"*30)
        function_name = jd.function
        user_function = import_string(function_name)
        print(user_function(**pl.payload))
        print("*"*30)
    except Exception as e:
        print(e)

    sys_modules_after = list(sys.modules)
    added_keys = list(set(sys_modules_after) - set(sys_modules_before))
    
    for k in added_keys:
        sys.modules.pop(k)

    sys.path.remove(package_path)


# @receiver(post_save, sender=JobDef)
# def create_job_payload_for_new_jobdef_signal(sender, instance, created, **kwargs):  # noqa
#     """
#     Create initial JobPayload when we create a JobDef and set it to active.

#     FIXME:
#         - check with the owner approach, if the property name or field changes
#           in relation to the permission system approach, we will have to
#           adjust accordingly.
#     """
#     if created:
#         try:
#             JobPayload.objects.create(jobdef=instance,
#                                       owner=instance.owner)
#         except Exception as exc:
#             # FIXME: need custom exception for more context
#             raise Exception("CUSTOM job plumbing Exception: {}".format(exc))


@receiver(post_save, sender=JobRun)
def create_job_output_for_new_jobrun_signal(sender, instance, created, **kwargs):  # noqa
    """
    Create a JobOutput everytime a JobRun gets created.

    FIXME:
        - check with the owner approach, if the property name or field changes
          in relation to the permission system approach, we will have to
          adjust accordingly.
    """
    if created:
        try:
            JobOutput.objects.create(jobrun=instance,
                                     jobdef=instance.jobdef.uuid,
                                     owner=instance.owner)
        except Exception as exc:
            # FIXME: need custom exception for more context
            raise Exception("CUSTOM job plumbing Exception: {}".format(exc))


@receiver(post_save, sender=JobRun)
def create_job_for_celery(sender, instance, created, **kwargs):  # noqa
    """
    Every time a new record is created, send the new job to celery
    """
    if created:
        # print(instance.uuid, instance.short_uuid)
        on_commit(lambda: start_jobrun.delay(instance.uuid))
