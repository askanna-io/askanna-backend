from django.db import migrations
from job.models import RunMetrics, RunMetricsRow, RunVariables
from job.tasks.metrics import post_run_deduplicate_metrics
from job.tasks.variables import post_run_deduplicate_variables


def update_metrics_and_variables_meta(apps, schema_editor):
    # Run the deduplication tasks for metrics and variables. This task will remove duplicate metrics & variables, and
    # it will update the meta data of these objects.

    runmetrics = RunMetrics.objects.all()
    for runmetric in runmetrics:
        try:
            post_run_deduplicate_metrics(runmetric.short_uuid)
        except AttributeError:
            metrics = RunMetricsRow.objects.filter(run_suuid=runmetric.short_uuid)
            for metric in metrics:
                if type(metric.metric) == list and len(metric.metric) == 1:
                    metric.metric = metric.metric[0]
                    metric.save(update_fields=["metric"])
            post_run_deduplicate_metrics(runmetric.short_uuid)

    runvariables = RunVariables.objects.all()
    for runvariable in runvariables:
        post_run_deduplicate_variables(runvariable.short_uuid)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0002_refactor_metricsmeta_and_runvariablesmeta"),
    ]

    operations = [
        migrations.RunPython(update_metrics_and_variables_meta, reverse_func, elidable=True),
    ]
