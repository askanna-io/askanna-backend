# Generated by Django 3.2.16 on 2023-01-05 14:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('run', '0018_auto_20230105_0940'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RunMetric',
            new_name='RunMetricMeta',
        ),
        migrations.RenameModel(
            old_name='RunVariable',
            new_name='RunVariableMeta',
        ),
        migrations.AlterModelOptions(
            name='runmetricrow',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='runvariablerow',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelTable(
            name='runmetricmeta',
            table='run_metric_meta',
        ),
        migrations.AlterModelTable(
            name='runmetricrow',
            table='run_metric_row',
        ),
        migrations.AlterModelTable(
            name='runvariablemeta',
            table='run_variable_meta',
        ),
        migrations.AlterModelTable(
            name='runvariablerow',
            table='run_variable_row',
        ),
    ]
