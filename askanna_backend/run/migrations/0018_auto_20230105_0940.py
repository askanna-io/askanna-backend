from django.db import migrations, models
import django.db.models.deletion


def forwards_func(apps, schema_editor):
    Run = apps.get_model("run", "Run")  # noqa: N806

    RunMetricRow = apps.get_model("run", "RunMetricRow")  # noqa: N806
    for obj in RunMetricRow.objects.all():
        obj.run = Run.objects.get(suuid=obj.run_suuid)
        obj.save()

    RunVariableRow = apps.get_model("run", "RunVariableRow")  # noqa: N806
    for obj in RunVariableRow.objects.all():
        obj.run = Run.objects.get(suuid=obj.run_suuid)
        obj.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("run", "0017_auto_20221229_1112"),
    ]

    operations = [
        migrations.AddField(
            model_name="runmetricrow",
            name="run",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="metrics", to="run.run"
            ),
        ),
        migrations.AddField(
            model_name="runvariablerow",
            name="run",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="variables", to="run.run"
            ),
        ),
        migrations.AlterField(
            model_name="runmetric",
            name="run",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="metrics_meta", to="run.run"
            ),
        ),
        migrations.AlterField(
            model_name="runvariable",
            name="run",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="variables_meta", to="run.run"
            ),
        ),
        migrations.RunPython(forwards_func, reverse_func),
        migrations.AlterField(
            model_name="runmetricrow",
            name="run",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="metrics", to="run.run"),
        ),
        migrations.AlterField(
            model_name="runvariablerow",
            name="run",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="variables", to="run.run"
            ),
        ),
    ]
