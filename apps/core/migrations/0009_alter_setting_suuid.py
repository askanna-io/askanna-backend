# Generated by Django 4.2.8 on 2024-01-04 12:33

import core.utils.suuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_remove_blob_dir"),
    ]

    operations = [
        migrations.AlterField(
            model_name="setting",
            name="suuid",
            field=models.CharField(
                default=core.utils.suuid.create_suuid, editable=False, max_length=32, unique=True, verbose_name="SUUID"
            ),
        ),
    ]
