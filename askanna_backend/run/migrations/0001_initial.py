# Generated by Django 3.2.15 on 2022-09-13 13:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("job", "__first__"),
        ("package", "__first__"),
        ("account", "0002_alter_user_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Run",
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
                        (
                            "jobid",
                            models.CharField(
                                blank=True, help_text="The job-id of the Celery run", max_length=120, null=True
                            ),
                        ),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("SUBMITTED", "SUBMITTED"),
                                    ("PENDING", "PENDING"),
                                    ("IN_PROGRESS", "IN_PROGRESS"),
                                    ("COMPLETED", "COMPLETED"),
                                    ("FAILED", "FAILED"),
                                ],
                                max_length=20,
                            ),
                        ),
                        ("trigger", models.CharField(blank=True, default="API", max_length=20, null=True)),
                        ("started", models.DateTimeField(editable=False, null=True)),
                        ("finished", models.DateTimeField(editable=False, null=True)),
                        (
                            "duration",
                            models.PositiveIntegerField(
                                blank=True, editable=False, help_text="Duration of the run in seconds", null=True
                            ),
                        ),
                        ("environment_name", models.CharField(default="", max_length=256)),
                        ("timezone", models.CharField(default="UTC", max_length=256)),
                        (
                            "created_by",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        ("jobdef", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="job.jobdef")),
                        (
                            "member",
                            models.ForeignKey(
                                null=True, on_delete=django.db.models.deletion.CASCADE, to="account.membership"
                            ),
                        ),
                        (
                            "package",
                            models.ForeignKey(
                                null=True, on_delete=django.db.models.deletion.CASCADE, to="package.package"
                            ),
                        ),
                        (
                            "payload",
                            models.ForeignKey(
                                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="job.jobpayload"
                            ),
                        ),
                        (
                            "run_image",
                            models.ForeignKey(
                                null=True, on_delete=django.db.models.deletion.SET_NULL, to="job.runimage"
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Job Run",
                        "verbose_name_plural": "Job Runs",
                        "ordering": ["-created"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
