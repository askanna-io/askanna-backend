from django.conf import settings
from django.db.models.signals import post_save, pre_delete, pre_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from config.celery_app import app as celery_app

from account.models.membership import MSP_WORKSPACE
from run.models import Run, RunLog, RunMetricMeta, RunVariable, RunVariableMeta


@receiver(post_save, sender=Run)
def create_run_log_for_new_run_signal(sender, instance, created, **kwargs):
    """
    Create a RunLog everytime a Run gets created.
    """
    if created:
        try:
            RunLog.objects.create(run=instance)
        except Exception as exc:
            raise Exception(f"Issue creating a RunLog: {exc}") from exc


@receiver(post_save, sender=Run)
def create_job_for_celery(sender, instance, created, **kwargs):
    """
    Every time a new record is created, send the new job to celery
    """
    if created:
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.start_run",
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
                kwargs={"run_uuid": instance.uuid},
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
                kwargs={"run_uuid": instance.uuid},
            )
        )


@receiver(post_save, sender=Run)
def create_runvariable(sender, instance, created, **kwargs):
    """
    Create intermediate model to store variables for a run
    """
    if created:
        RunVariableMeta.objects.create(**{"run": instance})


@receiver(pre_save, sender=Run)
def add_created_by_member_to_run(sender, instance: Run, **kwargs):
    """
    On creation of the run, add the member to it who created this. We already have the user, but we lookup the
    membership for it. We know this by job->project->workspace.
    """
    if instance.created_by_user and (not instance.created_by_member):
        workspace = instance.jobdef.project.workspace
        membership = (
            instance.created_by_user.memberships.filter(
                object_uuid=workspace.uuid,
                object_type=MSP_WORKSPACE,
                deleted_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if membership:
            instance.created_by_member = membership


@receiver(post_save, sender=RunMetricMeta)
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
            kwargs={"metric_meta_uuid": instance.uuid},
        )
    )


@receiver(post_save, sender=RunMetricMeta)
def move_metrics_to_rows(sender, instance, created, **kwargs):
    """
    After saving metric, we save the individual rows to a new table which allows us to query the metrics
    """
    update_fields = kwargs.get("update_fields")
    if update_fields:
        return

    if settings.TEST:
        from run.tasks import move_metrics_to_rows

        move_metrics_to_rows(**{"metric_meta_uuid": instance.uuid})
    else:
        on_commit(
            lambda: celery_app.send_task(
                "run.tasks.move_metrics_to_rows",
                kwargs={"metric_meta_uuid": instance.uuid},
            )
        )


@receiver(pre_delete, sender=RunMetricMeta)
def delete_runmetric(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=RunVariableMeta)
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
            kwargs={"variable_meta_uuid": instance.uuid},
        )
    )


@receiver(post_save, sender=RunVariableMeta)
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

        move_variables_to_rows(**{"variable_meta_uuid": instance.uuid})
    else:
        on_commit(
            lambda: celery_app.send_task(
                "run.tasks.move_variables_to_rows",
                kwargs={"variable_meta_uuid": instance.uuid},
            )
        )


@receiver(pre_save, sender=RunVariable)
def mask_secret_variables(sender, instance, **kwargs):
    """
    Only operate on RunVariable which are not yet marked as is_masked
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


@receiver(pre_delete, sender=RunVariableMeta)
def delete_runvariable(sender, instance, **kwargs):
    instance.prune()
