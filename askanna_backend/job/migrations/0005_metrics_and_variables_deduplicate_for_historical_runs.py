from django.db import migrations
from job.models import RunMetrics, RunVariables
from job.tasks.metrics import post_run_deduplicate_metrics
from job.tasks.variables import post_run_deduplicate_variables


def deduplicate_metrics_and_variables(apps, schema_editor):
    # Run the deduplication tasks for metrics and variables. This task will remove duplicate metrics & variables, and
    # it will update the meta data of these objects.

    runmetrics = RunMetrics.objects.all()
    for runmetric in runmetrics:
        post_run_deduplicate_metrics(runmetric.short_uuid)

    runvariables = RunVariables.objects.all()
    for runvariable in runvariables:
        post_run_deduplicate_variables(runvariable.short_uuid)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0004_changes_for_django_admin"),
    ]

    operations = [
        migrations.RunPython(deduplicate_metrics_and_variables, reverse_func, elidable=True),
    ]
