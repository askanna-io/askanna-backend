# Generated by Django 3.2.18 on 2023-02-28 11:26

import core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0007_add_at_suffix_to_datetime_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='package',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
    ]
