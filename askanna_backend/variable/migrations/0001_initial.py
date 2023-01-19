from django.db import migrations, models
import django.db.models.deletion
import django_cryptography.fields
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0010_move_projectvariable"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Variable",
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
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                                verbose_name="UUID",
                            ),
                        ),
                        (
                            "suuid",
                            models.CharField(
                                editable=False,
                                max_length=32,
                                unique=True,
                                verbose_name="SUUID",
                            ),
                        ),
                        ("name", models.CharField(max_length=128)),
                        (
                            "value",
                            django_cryptography.fields.encrypt(models.TextField(blank=True, default=None, null=True)),
                        ),
                        ("is_masked", models.BooleanField(default=False)),
                        (
                            "project",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="variable",
                                to="project.project",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Variable",
                        "verbose_name_plural": "Variables",
                        "db_table": "variable_variable",
                        "ordering": ["-created"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
