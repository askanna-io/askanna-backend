# Generated by Django 3.2.15 on 2022-09-13 13:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("run", "__first__"),
        ("job", "0001_initial_squashed_20220901"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="jobartifact",
                    name="jobrun",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="artifact", to="run.Run"
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="joboutput",
                    name="jobrun",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="output", to="run.Run"
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="runmetrics",
                    name="jobrun",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="metrics", to="run.Run"
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="runresult",
                    name="run",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="result", to="run.Run"
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="runvariables",
                    name="jobrun",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="runvariables", to="run.Run"
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="JobRun",
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="JobRun",
                    table="run_run",
                ),
            ],
        ),
    ]
