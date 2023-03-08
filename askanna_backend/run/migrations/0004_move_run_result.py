# Generated by Django 3.2.15 on 2022-09-22 14:38

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("run", "0003_update_meta_data"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Result",
                    fields=[
                        (
                            "created",
                            django_extensions.db.fields.CreationDateTimeField(
                                auto_now_add=True, verbose_name="created"
                            ),
                        ),
                        (
                            "modified",
                            django_extensions.db.fields.ModificationDateTimeField(
                                auto_now=True, verbose_name="modified"
                            ),
                        ),
                        ("deleted", models.DateTimeField(blank=True, null=True)),
                        ("description", models.TextField(blank=True, null=True, verbose_name="description")),
                        ("name", models.CharField(blank=True, max_length=255, null=True, verbose_name="name")),
                        (
                            "uuid",
                            models.UUIDField(
                                db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                            ),
                        ),
                        ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                        ("job", models.UUIDField(blank=True, editable=False, null=True)),
                        (
                            "mime_type",
                            models.CharField(
                                blank=True,
                                help_text="Storing the mime-type of the output file",
                                max_length=100,
                                null=True,
                            ),
                        ),
                        (
                            "size",
                            models.PositiveIntegerField(
                                default=0, editable=False, help_text="Size of the result stored"
                            ),
                        ),
                        (
                            "run",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE, related_name="result", to="run.run"
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Run result",
                        "verbose_name_plural": "Run results",
                        "ordering": ["-created"],
                    },
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="ChunkedResultPart",
                    fields=[
                        (
                            "created",
                            django_extensions.db.fields.CreationDateTimeField(
                                auto_now_add=True, verbose_name="created"
                            ),
                        ),
                        (
                            "modified",
                            django_extensions.db.fields.ModificationDateTimeField(
                                auto_now=True, verbose_name="modified"
                            ),
                        ),
                        ("deleted", models.DateTimeField(blank=True, null=True)),
                        (
                            "uuid",
                            models.UUIDField(
                                db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                            ),
                        ),
                        ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                        ("filename", models.CharField(max_length=500)),
                        ("size", models.IntegerField(help_text="Size of this run result")),
                        ("file_no", models.IntegerField()),
                        ("is_last", models.BooleanField(default=False)),
                        (
                            "runresult",
                            models.ForeignKey(
                                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="run.result"
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["-created"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]