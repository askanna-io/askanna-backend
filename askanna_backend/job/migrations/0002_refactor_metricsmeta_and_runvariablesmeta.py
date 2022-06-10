# Generated by Django 2.2.28 on 2022-06-09 08:16

import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_squashed_0035_merge_20210916_2355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='runmetrics',
            options={'ordering': ['-created'], 'verbose_name': 'Run Metric', 'verbose_name_plural': 'Run Metrics'},
        ),
        migrations.AlterModelOptions(
            name='runmetricsrow',
            options={'ordering': ['-created'], 'verbose_name': 'Run Metrics Row', 'verbose_name_plural': 'Run Metrics Rows'},
        ),
        migrations.AlterModelOptions(
            name='runvariablerow',
            options={'ordering': ['-created'], 'verbose_name': 'Run Variables Row', 'verbose_name_plural': 'Run Variables Rows'},
        ),
        migrations.AlterModelOptions(
            name='runvariables',
            options={'ordering': ['-created'], 'verbose_name': 'Run Variable', 'verbose_name_plural': 'Run Variables'},
        ),
        migrations.RemoveIndex(
            model_name='runmetricsrow',
            name='metric_json_index',
        ),
        migrations.RemoveIndex(
            model_name='runmetricsrow',
            name='label_json_index',
        ),
        migrations.RemoveIndex(
            model_name='runvariablerow',
            name='runvariable_var_json_idx',
        ),
        migrations.RemoveIndex(
            model_name='runvariablerow',
            name='runvariable_lbl_json_idx',
        ),
        migrations.RemoveField(
            model_name='jobrun',
            name='metric_keys',
        ),
        migrations.RemoveField(
            model_name='jobrun',
            name='metric_labels',
        ),
        migrations.RemoveField(
            model_name='jobrun',
            name='variable_keys',
        ),
        migrations.RemoveField(
            model_name='jobrun',
            name='variable_labels',
        ),
        migrations.AddField(
            model_name='runmetrics',
            name='label_names',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, editable=False, help_text='Unique metric label names and data type for metric label', null=True),
        ),
        migrations.AddField(
            model_name='runmetrics',
            name='metric_names',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, editable=False, help_text='Unique metric names and data type for metric', null=True),
        ),
        migrations.AddField(
            model_name='runvariables',
            name='label_names',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, editable=False, help_text='Unique variable label names and data type for variable label', null=True),
        ),
        migrations.AddField(
            model_name='runvariables',
            name='variable_names',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, editable=False, help_text='Unique variable names and data type for variable', null=True),
        ),
        migrations.AlterField(
            model_name='runmetrics',
            name='count',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='Count of metrics'),
        ),
        migrations.AlterField(
            model_name='runmetrics',
            name='size',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='File size of metrics JSON'),
        ),
        migrations.AlterField(
            model_name='runmetricsrow',
            name='label',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, editable=False, help_text='JSON field as list with multiple objects which are labels'),
        ),
        migrations.AlterField(
            model_name='runmetricsrow',
            name='metric',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, editable=False, help_text='JSON field as list with multiple objects which are metrics, but we limit to one'),
        ),
        migrations.AlterField(
            model_name='runvariablerow',
            name='label',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, editable=False, help_text='JSON field as list with multiple objects which are labels'),
        ),
        migrations.AlterField(
            model_name='runvariablerow',
            name='variable',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, editable=False, help_text='JSON field to store a variable'),
        ),
        migrations.AlterField(
            model_name='runvariables',
            name='count',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='Count of variables'),
        ),
        migrations.AlterField(
            model_name='runvariables',
            name='size',
            field=models.PositiveIntegerField(default=0, editable=False, help_text='File size of variables JSON'),
        ),
        migrations.AddIndex(
            model_name='runmetricsrow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['metric'], name='runmetric_metric_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddIndex(
            model_name='runmetricsrow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['label'], name='runmetric_label_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddIndex(
            model_name='runvariablerow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['variable'], name='runvariable_variable_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddIndex(
            model_name='runvariablerow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['label'], name='runvariable_label_json_idx', opclasses=['jsonb_path_ops']),
        ),
    ]