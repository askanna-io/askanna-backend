# -*- coding: utf-8 -*-
import datetime

from celery import shared_task

from job.models import (
    RunMetrics,
    RunMetricsRow,
)


@shared_task(bind=True, name="job.tasks.extract_metrics_meta")
def extract_metrics_meta(self, metrics_uuid):
    """
    Extract meta information from metrics and store the meta information in runmetrics object
    """
    runmetrics = RunMetrics.objects.get(pk=metrics_uuid)
    runmetrics.update_meta()


@shared_task(bind=True, name="job.tasks.move_metrics_to_rows")
def move_metrics_to_rows(self, metrics_uuid):
    runmetrics = RunMetrics.objects.get(pk=metrics_uuid)

    # remove old rows if any
    RunMetricsRow.objects.filter(run_suuid=runmetrics.short_uuid).delete()

    for metric in runmetrics.metrics:
        metric["created"] = datetime.datetime.fromisoformat(metric["created"])
        metric["project_suuid"] = runmetrics.jobrun.jobdef.project.short_uuid
        metric["job_suuid"] = runmetrics.jobrun.jobdef.short_uuid
        # overwrite run_suuid, even if the run_suuid defined is not right, prevent polution
        metric["run_suuid"] = runmetrics.jobrun.short_uuid

        RunMetricsRow.objects.create(**metric)

    runmetrics.update_meta()


@shared_task(bind=True, name="job.tasks.post_run_deduplicate_metrics")
def post_run_deduplicate_metrics(self, run_suuid):
    """
    Remove double run metrics if any
    """
    metrics = RunMetricsRow.objects.filter(run_suuid=run_suuid).order_by("created")
    last_metric = None
    for metric in metrics:
        if metric == last_metric:
            metric.delete()
        last_metric = metric

    runmetrics = RunMetrics.objects.get(jobrun__short_uuid=run_suuid)
    runmetrics.update_meta()
