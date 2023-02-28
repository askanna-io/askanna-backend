import datetime

from celery import shared_task
from run.models import RunMetric, RunMetricMeta


@shared_task(bind=True, name="run.tasks.extract_run_metric_meta")
def extract_run_metric_meta(self, metric_meta_uuid):
    """
    Extract meta information from metrics and store the meta information in runmetric object
    """
    run_metric_meta = RunMetricMeta.objects.get(pk=metric_meta_uuid)
    run_metric_meta.update_meta()


@shared_task(bind=True, name="run.tasks.move_metrics_to_rows")
def move_metrics_to_rows(self, metric_meta_uuid):
    run_metric_meta = RunMetricMeta.objects.get(pk=metric_meta_uuid)

    # Remove old rows if any
    RunMetric.objects.filter(run=run_metric_meta.run).delete()

    for metric in run_metric_meta.metrics:
        metric["created_at"] = datetime.datetime.fromisoformat(metric["created_at"])
        metric["project_suuid"] = run_metric_meta.run.jobdef.project.suuid
        metric["job_suuid"] = run_metric_meta.run.jobdef.suuid
        metric["run_suuid"] = run_metric_meta.run.suuid
        metric["run"] = run_metric_meta.run

        RunMetric.objects.create(**metric)

    run_metric_meta.update_meta()


@shared_task(bind=True, name="run.tasks.post_run_deduplicate_metrics")
def post_run_deduplicate_metrics(self, run_uuid):
    """
    Remove double run metrics if any
    """
    metrics = RunMetric.objects.filter(run__pk=run_uuid).order_by("created_at", "metric")
    last_metric = None
    for metric in metrics:
        if last_metric and (
            metric.metric == last_metric.metric
            and metric.label == last_metric.label
            and metric.created_at == last_metric.created_at
        ):
            metric.delete()
        last_metric = metric

    try:
        run_metric = RunMetricMeta.objects.get(run__pk=run_uuid)
    except RunMetricMeta.DoesNotExist:
        pass
    else:
        run_metric.update_meta()
