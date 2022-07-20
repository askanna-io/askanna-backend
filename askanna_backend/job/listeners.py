import os
from zipfile import ZipFile

from core.utils import detect_file_mimetype
from django.conf import settings
from django.db.models.signals import post_save, pre_delete, pre_save
from django.db.transaction import on_commit
from django.dispatch import receiver
from job.models import (
    JobArtifact,
    JobOutput,
    JobPayload,
    JobRun,
    RunMetrics,
    RunResult,
    RunVariableRow,
    RunVariables,
)
from job.signals import artifact_upload_finish, result_upload_finish
from users.models import MSP_WORKSPACE

from config.celery_app import app as celery_app


@receiver(result_upload_finish)
def handle_result_upload(sender, signal, postheaders, obj, **kwargs):
    """
    After saving the result, determine the mime-type of the file using python-magic
    and custom logic to determine specific filetypes
    """
    detected_mimetype = detect_file_mimetype(obj.stored_path)
    if detect_file_mimetype:
        update_fields = ["mime_type"]
        obj.mime_type = detected_mimetype
        obj.save(update_fields=update_fields)


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


@receiver(pre_delete, sender=RunResult)
def delete_runresult(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=JobRun)
def create_job_output_for_new_jobrun_signal(sender, instance, created, **kwargs):
    """
    Create a JobOutput everytime a JobRun gets created.
    """
    if created:
        try:
            JobOutput.objects.create(jobrun=instance, jobdef=instance.jobdef.uuid, owner=instance.owner)
        except Exception as exc:
            raise Exception("Issue creating a JobOutput: {}".format(exc))


@receiver(post_save, sender=JobRun)
def create_job_for_celery(sender, instance, created, **kwargs):  # noqa
    """
    Every time a new record is created, send the new job to celery
    """
    if created:
        # on_commit(lambda: start_run.delay(instance.uuid))
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.start_run",
                args=None,
                kwargs={"run_uuid": instance.uuid},
            )
        )


@receiver(post_save, sender=JobRun)
def post_run_deduplicate_metrics(sender, instance, created, **kwargs):  # noqa
    """
    Fix metrics after job is finished
    """
    if instance.is_finished:
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.post_run_deduplicate_metrics",
                args=None,
                kwargs={"run_suuid": instance.short_uuid},
            )
        )


@receiver(post_save, sender=JobRun)
def post_run_deduplicate_variables(sender, instance, created, **kwargs):  # noqa
    """
    Fix variables after job is finished
    """
    if instance.is_finished:
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.post_run_deduplicate_variables",
                args=None,
                kwargs={"run_suuid": instance.short_uuid},
            )
        )


@receiver(post_save, sender=JobRun)
def create_runvariables(sender, instance, created, **kwargs):
    """
    Create intermediate model to store variables for a run
    """
    if created:
        RunVariables.objects.create(**{"jobrun": instance})


@receiver(pre_save, sender=JobRun)
def add_member_to_jobrun(sender, instance, **kwargs):
    """
    On creation of the jobrun, add the member to it who created this. We already have the user, but we lookup the
    membership for it. We know this by job->project->workspace.
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
def extract_meta_from_metrics(sender, instance, created, **kwargs):
    """
    After saving metrics, we want to update the metrics meta information in RunInfo.
    """
    update_fields = kwargs.get("update_fields")
    if update_fields:
        # We don't do anything if this was an update on specific fields
        return

    on_commit(
        lambda: celery_app.send_task(
            "job.tasks.extract_metrics_meta",
            args=None,
            kwargs={"metrics_uuid": instance.uuid},
        )
    )


@receiver(post_save, sender=RunMetrics)
def move_metrics_to_rows(sender, instance, created, **kwargs):
    """
    After saving metrics, we save the individueal rows to
    a new table which allows us to query the metrics
    """
    update_fields = kwargs.get("update_fields")
    if update_fields:
        # we don't do anything if this was an update on specific fields
        return

    if settings.TEST:
        from job.tasks import move_metrics_to_rows

        move_metrics_to_rows(**{"metrics_uuid": instance.uuid})
    else:
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.move_metrics_to_rows",
                args=None,
                kwargs={"metrics_uuid": instance.uuid},
            )
        )


@receiver(pre_delete, sender=RunMetrics)
def delete_runmetrics(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=RunVariables)
def extract_meta_from_variables(sender, instance, created, **kwargs):
    """
    After saving tracked variables, we want to update the variables meta information in runinfo.
    """
    update_fields = kwargs.get("update_fields")
    if update_fields or created:
        # We don't do anything if this was an update on specific fields
        return

    on_commit(
        lambda: celery_app.send_task(
            "job.tasks.extract_variables_meta",
            args=None,
            kwargs={"variables_uuid": instance.uuid},
        )
    )


@receiver(post_save, sender=RunVariables)
def move_variables_to_rows(sender, instance, created, **kwargs):
    """
    After saving variables, we save the individual rows to
    a new table that allows us to query the variables
    """
    update_fields = kwargs.get("update_fields")
    if update_fields or created:
        # we don't do anything if this was an update on specific fields
        return

    if settings.TEST:
        from job.tasks import move_variables_to_rows

        move_variables_to_rows(**{"variables_uuid": instance.uuid})
    else:
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.move_variables_to_rows",
                args=None,
                kwargs={"variables_uuid": instance.uuid},
            )
        )


@receiver(pre_save, sender=RunVariableRow)
def mask_secret_variables(sender, instance, **kwargs):
    """
    Only operate on RunVariableRow which are not yet marked as is_masked
    We check this before actually saving to the database, giving us a chance
    to modify this

    An instance is not masked yet, if it was coming from the API (SDK call)

    """
    if not instance.is_masked:
        variable_name = instance.variable.get("name").upper()
        is_masked = any(
            [
                "KEY" in variable_name,
                "TOKEN" in variable_name,
                "SECRET" in variable_name,
                "PASSWORD" in variable_name,
            ]
        )
        if is_masked:
            instance.variable["value"] = "***masked***"
            instance.is_masked = True
            # add the tag is_masked, but first check whether this is already in the instance.label
            has_is_masked = "is_masked" in [label.get("name") for label in instance.label]
            if not has_is_masked:
                instance.label.append({"name": "is_masked", "value": None, "type": "tag"})


@receiver(pre_delete, sender=RunVariables)
def delete_runvariables(sender, instance, **kwargs):
    instance.prune()
