# Generated by Django 3.2.16 on 2023-01-17 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('run', '0019_auto_20230105_1456'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='run',
            index=models.Index(fields=['name', 'created'], name='run_run_name_6643c9_idx'),
        ),
    ]