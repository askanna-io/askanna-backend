# Generated by Django 3.2.18 on 2023-02-28 11:26

from django.db import migrations

import core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('run', '0021_add_at_suffix_to_datetime_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chunkedrunartifactpart',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='chunkedrunartifactpart',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='chunkedrunresultpart',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='chunkedrunresultpart',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runartifact',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='runartifact',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runlog',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='runlog',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runmetricmeta',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='runmetricmeta',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runmetricrow',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runresult',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='runresult',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runvariablemeta',
            name='created_at',
            field=core.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='runvariablemeta',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='runvariablerow',
            name='modified_at',
            field=core.fields.ModificationDateTimeField(auto_now=True),
        ),
    ]
