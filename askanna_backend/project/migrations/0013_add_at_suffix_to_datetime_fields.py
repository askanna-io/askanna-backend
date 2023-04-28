# Generated by Django 3.2.17 on 2023-02-22 14:05

import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("project", "0012_add_db_index"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="project",
            name="project_pro_name_8c034f_idx",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.AlterField(
            model_name="project",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["name", "created_at"], name="project_pro_name_b74a75_idx"),
        ),
    ]
