import os
from zipfile import ZipFile

from config.celery_app import app as celery_app
from django.conf import settings
from django.db.models.signals import pre_delete, pre_save, post_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from job.models import JobArtifact, JobOutput, JobPayload, JobRun, RunMetrics
from job.signals import artifact_upload_finish
from job.tasks import start_jobrun_dockerized, extract_metrics_labels
from users.models import MSP_WORKSPACE


@receiver(artifact_upload_finish)
def handle_upload(sender, signal, postheaders, obj, **kwargs):
    """
    After saving the artifact, we extract the contents of the artifact to
    BLOB_ROOT, which is served on the CDN to allow us to retrieve the individual
    files one by one.
    """
    source_location = settings.ARTIFACTS_ROOT
    target_location = settings.BLOB_ROOT

    source_path = os.path.join(source_location, obj.storage_location, obj.filename)
    target_path = os.path.join(target_location, str(obj.uuid))

    with ZipFile(source_path) as zippackage:
        zippackage.extractall(path=target_path)


@receiver(pre_delete, sender=JobArtifact)
def delete_artifact(sender, instance, **kwargs):
    instance.prune()


@receiver(pre_delete, sender=JobOutput)
def delete_joboutput(sender, instance, **kwargs):
    instance.prune()


@receiver(pre_delete, sender=JobPayload)
def delete_jobpayload(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=JobRun)
def create_job_output_for_new_jobrun_signal(sender, instance, created, **kwargs):
    """
    Create a JobOutput everytime a JobRun gets created.
    """
    if created:
        try:
            JobOutput.objects.create(
                jobrun=instance, jobdef=instance.jobdef.uuid, owner=instance.owner
            )
        except Exception as exc:
            # FIXME: need custom exception for more context
            raise Exception("CUSTOM job plumbing Exception: {}".format(exc))


@receiver(post_save, sender=JobRun)
def create_job_for_celery(sender, instance, created, **kwargs):  # noqa
    """
    Every time a new record is created, send the new job to celery
    """
    if created:
        on_commit(lambda: start_jobrun_dockerized.delay(instance.uuid))


@receiver(pre_save, sender=JobRun)
def add_member_to_jobrun(sender, instance, **kwargs):
    """
    On creation of the jobrun, add the member to it who created this.
    We already thave the user, but we lookup the membership for it
    (we know this by job->project->workspace)
    """
    if not instance.member:
        # first lookup which member this could be based on workspace
        in_workspace = instance.jobdef.project.workspace
        member_query = instance.owner.memberships.filter(
            object_uuid=in_workspace.uuid,
            object_type=MSP_WORKSPACE,
            deleted__isnull=True,
        )
        if member_query.exists():
            # get the membership out of it
            membership = member_query.first()
            if membership:
                instance.member = membership


@receiver(post_save, sender=RunMetrics)
def extract_labels_from_metrics_to_jobrun(sender, instance, created, **kwargs):
    """
    After saving metrics, we want to update the linked
    JobRun.labels to put the static labels in there
    We don't do this in a django instance, we delegate this
    to a celery task.
    """

    update_fields = kwargs.get("update_fields")
    if update_fields:
        # we don't do anything if this was an update on specific fields
        return

    # on_commit(lambda: extract_metrics_labels.delay(instance.uuid))
    on_commit(
        lambda: celery_app.send_task(
            "job.tasks.extract_metrics_labels",
            args=None,
            kwargs={"metrics_uuid": instance.uuid},
        )
    )
