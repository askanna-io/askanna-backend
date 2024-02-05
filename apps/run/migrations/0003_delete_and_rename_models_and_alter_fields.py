# Generated by Django 4.2.7 on 2023-11-28 09:26

import django.db.models.deletion
from django.db import migrations, models

import core.utils.suuid


class Migration(migrations.Migration):
    dependencies = [
        ("run", "0002_update_run_created_by"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ChunkedRunArtifactPart",
        ),
        migrations.DeleteModel(
            name="ChunkedRunResultPart",
        ),
        migrations.DeleteModel(
            name="RunMetricMeta",
        ),
        migrations.DeleteModel(
            name="RunVariableMeta",
        ),
        migrations.RenameModel(
            old_name="RunMetricRow",
            new_name="RunMetric",
        ),
        migrations.RenameModel(
            old_name="RunVariableRow",
            new_name="RunVariable",
        ),
        migrations.AlterModelTable(
            name="runmetric",
            table="run_metric",
        ),
        migrations.AlterModelTable(
            name="runvariable",
            table="run_variable",
        ),
        migrations.AlterField(
            model_name="runartifact",
            name="run",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="artifacts", to="run.run"
            ),
        ),
        migrations.AlterField(
            model_name="runresult",
            name="run",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name="archive_result", to="run.run"
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
        migrations.AlterField(
            model_name="runartifact",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
        migrations.AlterField(
            model_name="runlog",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
        migrations.AlterField(
            model_name="runmetric",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
        migrations.AlterField(
            model_name="runmetric",
            name="metric",
            field=models.JSONField(
                editable=False,
                help_text="JSON field as list with multiple objects which are metrics, but we limit to one",
            ),
        ),
        migrations.AlterField(
            model_name="runmetric",
            name="label",
            field=models.JSONField(
                default=None,
                editable=False,
                help_text="JSON field as list with multiple objects which are labels",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="runmetric",
            name="created_at",
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="runresult",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
        migrations.AlterField(
            model_name="runvariable",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
        migrations.AlterField(
            model_name="runvariable",
            name="variable",
            field=models.JSONField(editable=False, help_text="JSON field to store a variable"),
        ),
        migrations.AlterField(
            model_name="runvariable",
            name="label",
            field=models.JSONField(
                default=None,
                editable=False,
                help_text="JSON field as list with multiple objects which are labels",
                null=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="runartifact",
            options={"get_latest_by": "created_at", "ordering": ["-created_at"]},
        ),
    ]