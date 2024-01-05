# Generated by Django 4.2.8 on 2024-01-04 12:33

import core.utils.suuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0002_update_workspace_created_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workspace",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
    ]
