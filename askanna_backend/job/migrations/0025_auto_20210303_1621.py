# Generated by Django 2.2.8 on 2021-03-03 16:21

import core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0024_auto_20210216_0904"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="jobdef",
            name="backend",
        ),
        migrations.RemoveField(
            model_name="jobdef",
            name="default_payload",
        ),
        migrations.RemoveField(
            model_name="jobdef",
            name="env_variables",
        ),
        migrations.RemoveField(
            model_name="jobdef",
            name="environment",
        ),
        migrations.RemoveField(
            model_name="jobdef",
            name="function",
        ),
        migrations.RemoveField(
            model_name="jobdef",
            name="owner",
        ),
        migrations.RemoveField(
            model_name="jobdef",
            name="visible",
        ),
        migrations.AlterField(
            model_name="runmetricsrow",
            name="metric",
            field=core.fields.JSONField(
                help_text="JSON field as list with multiple objects which are metrics, but we limit to one"
            ),
        ),
    ]