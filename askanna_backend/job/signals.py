from django.db.models.signals import post_save
from django.dispatch import receiver

from job.models import (
    JobDef,
    JobRun,
    JobPayload,
    JobOutput,
)


@receiver(post_save, sender=JobDef)
def create_job_payload_for_new_jobdef_signal(sender, instance, created, **kwargs):  # noqa
    """
    Create initial JobPayload when we create a JobDef and set it to active.

    FIXME:
        - check with the owner approach, if the property name or field changes
          in relation to the permission system approach, we will have to
          adjust accordingly.
    """
    if created:
        try:
            JobPayload.objects.create(jobdef=instance,
                                      owner=instance.owner)
        except Exception as exc:
            # FIXME: need custom exception for more context
            raise Exception("CUSTOM job plumbing Exception: {}".format(exc))


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
