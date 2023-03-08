# Generated by Django 3.2.15 on 2022-09-27 11:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0006_move_projectvariable"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="RunMetricsRow",
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="RunMetricsRow",
                    table="run_metricrow",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="RunVariableRow",
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="RunVariableRow",
                    table="run_variablerow",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="RunMetrics",
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="RunMetrics",
                    table="run_metric",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="RunVariables",
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="RunVariables",
                    table="run_variable",
                ),
            ],
        ),
    ]