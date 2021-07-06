# -*- coding: utf-8 -*-
import datetime
import json

from celery import shared_task
from job.models import (
    RunMetrics,
    RunMetricsRow,
)


@shared_task(bind=True, name="job.tasks.extract_metrics_labels")
def extract_metrics_labels(self, metrics_uuid):
    """
    Extract labels in .metrics and store the list of labels in .jobrun.labels
    """
    runmetrics = RunMetrics.objects.get(pk=metrics_uuid)
    jobrun = runmetrics.jobrun
    if not runmetrics.metrics:
        # we don't have metrics stored, as this is None (by default on creation)
        return
    alllabels = []
    allkeys = []
    count = 0
    for metric in runmetrics.metrics[::]:
        labels = metric.get("label", [])
        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

        # count number of metrics
        metrics = metric.get("metric", {})
        allkeys.append(metrics.get("name"))
        count += 1

    jobrun.metric_keys = list(set(allkeys) - set([None]))
    jobrun.metric_labels = list(set(alllabels) - set([None]))
    jobrun.save(update_fields=["metric_labels", "metric_keys"])

    runmetrics.count = count
    runmetrics.size = len(json.dumps(runmetrics.metrics))
    runmetrics.save(update_fields=["count", "size"])


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
