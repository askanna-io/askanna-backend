import os
from zipfile import ZipFile

from core.utils import detect_file_mimetype, get_files_and_directories_in_zip_file
from django.conf import settings
from django.db.models.signals import post_save, pre_delete, pre_save
from django.db.transaction import on_commit
from django.dispatch import receiver
from run.models import (
    Run,
    RunArtifact,
    RunLog,
    RunMetric,
    RunResult,
    RunVariable,
    RunVariableRow,
)
from run.signals import artifact_upload_finish, result_upload_finish
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

    zip_list = get_files_and_directories_in_zip_file(source_path)
    obj.count_dir = sum(map(lambda x: x["type"] == "directory", zip_list))
    obj.count_files = sum(map(lambda x: x["type"] == "file", zip_list))
    obj.save(update_fields=["count_dir", "count_files"])

    with ZipFile(source_path, mode="r") as zip_file:
        zip_file.extractall(path=target_path)


@receiver(pre_delete, sender=RunArtifact)
def delete_artifact(sender, instance, **kwargs):
    instance.prune()


@receiver(pre_delete, sender=RunLog)
def delete_runlog(sender, instance, **kwargs):
    instance.prune()


@receiver(pre_delete, sender=RunResult)
def delete_runresult(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=Run)
def create_run_log_for_new_run_signal(sender, instance, created, **kwargs):
    """
    Create a RunLog everytime a Run gets created.
    """
    if created:
        try:
            RunLog.objects.create(run=instance)
        except Exception as exc:
            raise Exception("Issue creating a RunLog: {}".format(exc))


@receiver(post_save, sender=Run)
def create_job_for_celery(sender, instance, created, **kwargs):
    """
    Every time a new record is created, send the new job to celery
    """
    if created:
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.start_run",
                args=None,
                kwargs={"run_uuid": instance.uuid},
            )
        )


@receiver(post_save, sender=Run)
def post_run_deduplicate_metrics(sender, instance, created, **kwargs):
    """
    Fix metrics after job is finished
    """
    if instance.is_finished:
        on_commit(
            lambda: celery_app.send_task(
                "run.tasks.post_run_deduplicate_metrics",
                args=None,
                kwargs={"run_suuid": instance.short_uuid},
            )
        )


@receiver(post_save, sender=Run)
def post_run_deduplicate_variables(sender, instance, created, **kwargs):
    """
    Fix variables after job is finished
    """
    if instance.is_finished:
        on_commit(
            lambda: celery_app.send_task(
                "run.tasks.post_run_deduplicate_variables",
                args=None,
                kwargs={"run_suuid": instance.short_uuid},
            )
        )


@receiver(post_save, sender=Run)
def create_runvariable(sender, instance, created, **kwargs):
    """
    Create intermediate model to store variables for a run
    """
    if created:
        RunVariable.objects.create(**{"run": instance})


@receiver(pre_save, sender=Run)
def add_member_to_run(sender, instance, **kwargs):
    """
    On creation of the run, add the member to it who created this. We already have the user, but we lookup the
    membership for it. We know this by job->project->workspace.
    """
    if not instance.member:
        # first lookup which member this could be based on workspace
        in_workspace = instance.jobdef.project.workspace
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


@receiver(post_save, sender=RunMetric)
def extract_meta_from_metric(sender, instance, created, **kwargs):
    """
    After saving metrics, we want to update the run metric meta information
    """
    update_fields = kwargs.get("update_fields")
    if update_fields:
        return

    on_commit(
        lambda: celery_app.send_task(
            "run.tasks.extract_run_metric_meta",
            args=None,
            kwargs={"metrics_uuid": instance.uuid},
        )
    )


@receiver(post_save, sender=RunMetric)
def move_metrics_to_rows(sender, instance, created, **kwargs):
    """
    After saving metric, we save the individual rows to a new table which allows us to query the metrics
    """
    update_fields = kwargs.get("update_fields")
    if update_fields:
        return

    if settings.TEST:
        from run.tasks import move_metrics_to_rows

        move_metrics_to_rows(**{"metrics_uuid": instance.uuid})
    else:
        on_commit(
            lambda: celery_app.send_task(
                "run.tasks.move_metrics_to_rows",
                args=None,
                kwargs={"metrics_uuid": instance.uuid},
            )
        )


@receiver(pre_delete, sender=RunMetric)
def delete_runmetric(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=RunVariable)
def extract_meta_from_variable(sender, instance, created, **kwargs):
    """
    After saving tracked variables, we want to update the run variable meta information
    """
    update_fields = kwargs.get("update_fields")
    if update_fields or created:
        return

    on_commit(
        lambda: celery_app.send_task(
            "run.tasks.extract_run_variable_meta",
            args=None,
            kwargs={"variables_uuid": instance.uuid},
        )
    )


@receiver(post_save, sender=RunVariable)
def move_variables_to_rows(sender, instance, created, **kwargs):
    """
    After saving variables, we save the individual rows to
    a new table that allows us to query the variables
    """
    update_fields = kwargs.get("update_fields")
    if update_fields or created:
        return

    if settings.TEST:
        from run.tasks import move_variables_to_rows

        move_variables_to_rows(**{"variables_uuid": instance.uuid})
    else:
        on_commit(
            lambda: celery_app.send_task(
                "run.tasks.move_variables_to_rows",
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


@receiver(pre_delete, sender=RunVariable)
def delete_runvariable(sender, instance, **kwargs):
    instance.prune()
