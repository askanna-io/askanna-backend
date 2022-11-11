import datetime

from celery import shared_task
from run.models import RunMetric, RunMetricRow


@shared_task(bind=True, name="run.tasks.extract_run_metric_meta")
def extract_run_metric_meta(self, metrics_uuid):
    """
    Extract meta information from metrics and store the meta information in runmetric object
    """
    run_metric = RunMetric.objects.get(pk=metrics_uuid)
    run_metric.update_meta()


@shared_task(bind=True, name="run.tasks.move_metrics_to_rows")
def move_metrics_to_rows(self, metrics_uuid):
    run_metric = RunMetric.objects.get(pk=metrics_uuid)

    # Remove old rows if any
    RunMetricRow.objects.filter(run_suuid=run_metric.suuid).delete()

    for metric in run_metric.metrics:
        metric["created"] = datetime.datetime.fromisoformat(metric["created"])
        metric["project_suuid"] = run_metric.run.jobdef.project.suuid
        metric["job_suuid"] = run_metric.run.jobdef.suuid
        # Overwrite run_suuid, even if the run_suuid defined is not right, prevent polution
        metric["run_suuid"] = run_metric.run.suuid

        RunMetricRow.objects.create(**metric)

    run_metric.update_meta()


@shared_task(bind=True, name="run.tasks.post_run_deduplicate_metrics")
def post_run_deduplicate_metrics(self, run_suuid):
    """
    Remove double run metrics if any
    """
    metrics = RunMetricRow.objects.filter(run_suuid=run_suuid).order_by("created", "metric")
    last_metric = None
    for metric in metrics:
        if last_metric and (
            metric.metric == last_metric.metric
            and metric.label == last_metric.label
            and metric.created == last_metric.created
        ):
            metric.delete()
        last_metric = metric

    try:
        run_metric = RunMetric.objects.get(run__suuid=run_suuid)
    except RunMetric.DoesNotExist:
        pass
    else:
        run_metric.update_meta()
