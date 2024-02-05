# Generated by Django 4.2.7 on 2023-11-28 09:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("storage", "0001_initial"),
        ("run", "0003_delete_and_rename_models_and_alter_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="runartifact",
            name="size",
        ),
        migrations.RemoveField(
            model_name="runartifact",
            name="count_dir",
        ),
        migrations.RemoveField(
            model_name="runartifact",
            name="count_files",
        ),
        migrations.RemoveField(
            model_name="run",
            name="celery_task_id",
        ),
        migrations.RemoveField(
            model_name="runmetric",
            name="job_suuid",
        ),
        migrations.RemoveField(
            model_name="runmetric",
            name="project_suuid",
        ),
        migrations.RemoveField(
            model_name="runmetric",
            name="run_suuid",
        ),
        migrations.RemoveField(
            model_name="runvariable",
            name="job_suuid",
        ),
        migrations.RemoveField(
            model_name="runvariable",
            name="project_suuid",
        ),
        migrations.RemoveField(
            model_name="runvariable",
            name="run_suuid",
        ),
        migrations.RenameField(
            model_name="run",
            old_name="payload",
            new_name="archive_job_payload",
        ),
        migrations.AddField(
            model_name="run",
            name="payload_file",
            field=models.OneToOneField(
                help_text="File with the run payload in JSON format",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="run_payload_file",
                to="storage.file",
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="result_file",
            field=models.OneToOneField(
                help_text="File with the run result",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="run_result_file",
                to="storage.file",
            ),
        ),
        migrations.AddField(
            model_name="runartifact",
            name="artifact_file",
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="artifact_file", to="storage.file"
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="metrics_file",
            field=models.OneToOneField(
                help_text="File with the run metrics in JSON format",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="run_metrics_file",
                to="storage.file",
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="metrics_meta",
            field=models.JSONField(
                default=None, editable=False, help_text="Meta information about run metrics", null=True
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="variables_file",
            field=models.OneToOneField(
                help_text="File with the run variables in JSON format",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="run_variables_file",
                to="storage.file",
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="variables_meta",
            field=models.JSONField(
                default=None, editable=False, help_text="Meta information about run variables", null=True
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="exit_code",
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="log_file",
            field=models.OneToOneField(
                help_text="File with the run log in JSON format",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="run_log_file",
                to="storage.file",
            ),
        ),
    ]