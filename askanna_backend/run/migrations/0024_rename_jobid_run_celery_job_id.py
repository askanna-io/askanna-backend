# Generated by Django 4.1.7 on 2023-03-30 12:26

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("run", "0023_more_strict_in_allowing_null"),
    ]

    operations = [
        migrations.RenameField(
            model_name="run",
            old_name="jobid",
            new_name="celery_task_id",
        ),
    ]