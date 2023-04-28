# Generated by Django 3.2.18 on 2023-02-28 11:26

from django.db import migrations

import core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0016_add_at_suffix_to_datetime_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobdef',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='jobdef',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='jobpayload',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='jobpayload',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runimage',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='runimage',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='scheduledjob',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='scheduledjob',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
    ]
