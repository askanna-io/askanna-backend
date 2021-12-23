# Generated by Django 2.2.24 on 2021-10-24 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0008_project_visibility"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="visibility",
            field=models.CharField(
                db_index=True,
                default="PRIVATE",
                max_length=255,
                verbose_name="Visibility",
            ),
        ),
    ]