# Generated by Django 3.1.14 on 2022-09-01 12:26

import uuid

import django_cryptography.fields
import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Setting",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("name", models.CharField(blank=True, max_length=32, unique=True)),
                ("value", django_cryptography.fields.encrypt(models.TextField(blank=True, default=None, null=True))),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
