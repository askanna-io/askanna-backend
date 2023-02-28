# Generated by Django 3.2.17 on 2023-02-22 14:05

from django.db import migrations, models
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):
    dependencies = [
        ("run", "0020_add_db_index"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="run",
            name="run_run_name_6643c9_idx",
        ),
        migrations.RenameField(
            model_name="chunkedrunartifactpart",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="chunkedrunresultpart",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="run",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="run",
            old_name="finished",
            new_name="finished_at",
        ),
        migrations.RenameField(
            model_name="run",
            old_name="started",
            new_name="started_at",
        ),
        migrations.RenameField(
            model_name="runartifact",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="runlog",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="runmetricmeta",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="runmetricrow",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runmetricrow",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="runresult",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="runvariablemeta",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="runvariablerow",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runvariablerow",
            old_name="deleted",
            new_name="deleted_at",
        ),
        migrations.RenameField(
            model_name="chunkedrunartifactpart",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="chunkedrunartifactpart",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="chunkedrunresultpart",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="chunkedrunresultpart",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="run",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="run",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runartifact",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runartifact",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runlog",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runlog",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runmetricmeta",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runmetricmeta",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runmetricrow",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runresult",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runresult",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runvariablemeta",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="runvariablemeta",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.RenameField(
            model_name="runvariablerow",
            old_name="modified",
            new_name="modified_at",
        ),
        migrations.AlterField(
            model_name="chunkedrunartifactpart",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="chunkedrunartifactpart",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="chunkedrunresultpart",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="chunkedrunresultpart",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runartifact",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="runartifact",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runlog",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="runlog",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runmetricmeta",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="runmetricmeta",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runmetricrow",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runresult",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="runresult",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runvariablemeta",
            name="created_at",
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="runvariablemeta",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="runvariablerow",
            name="modified_at",
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True),
        ),
        migrations.AddIndex(
            model_name="run",
            index=models.Index(fields=["name", "created_at"], name="run_run_name_4fdc9b_idx"),
        ),
        migrations.AlterModelOptions(
            name="chunkedrunartifactpart",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Run artifact chunk",
                "verbose_name_plural": "Run artifacts chunks",
            },
        ),
        migrations.AlterModelOptions(
            name="chunkedrunresultpart",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Run result chunk",
                "verbose_name_plural": "Run result chunks",
            },
        ),
        migrations.AlterModelOptions(
            name="run",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runartifact",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runlog",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runmetricmeta",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runmetricrow",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runresult",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runvariablemeta",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="runvariablerow",
            options={"ordering": ["-created_at"]},
        ),
    ]
