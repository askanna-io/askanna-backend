# Generated by Django 2.2.8 on 2020-02-06 16:11

import core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flow', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flowrun',
            name='jobids',
            field=core.fields.JSONField(blank=True, null=True),
        ),
    ]
