# Generated by Django 4.1.8 on 2023-04-14 15:29

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import core.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Workspace",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="UUID"
                    ),
                ),
                ("suuid", models.CharField(editable=False, max_length=32, unique=True, verbose_name="SUUID")),
                ("created_at", core.fields.CreationDateTimeField(auto_now_add=True)),
                ("modified_at", core.fields.ModificationDateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("description", models.TextField(blank=True, default="")),
                ("name", models.CharField(db_index=True, default="New workspace", max_length=255)),
                (
                    "visibility",
                    models.CharField(
                        choices=[("PRIVATE", "PRIVATE"), ("PUBLIC", "PUBLIC")],
                        db_index=True,
                        default="PRIVATE",
                        max_length=10,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="workspace",
            index=models.Index(fields=["name", "created_at"], name="workspace_w_name_044646_idx"),
        ),
    ]