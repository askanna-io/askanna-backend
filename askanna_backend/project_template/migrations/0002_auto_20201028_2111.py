# Generated by Django 2.2.8 on 2020-10-28 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project_template', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projecttemplate',
            name='short_uuid',
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
    ]
