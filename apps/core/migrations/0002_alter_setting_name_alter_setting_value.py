# Generated by Django 4.2.1 on 2023-05-04 18:48

from django.db import migrations, models
import django_cryptography.fields


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial_20230414"),
    ]

    operations = [
        migrations.AlterField(
            model_name="setting",
            name="name",
            field=models.CharField(
                choices=[
                    ("ASKANNA_UI_URL", "ASKANNA_UI_URL"),
                    ("DEFAULT_FROM_EMAIL", "DEFAULT_FROM_EMAIL"),
                    ("DOCKER_AUTO_REMOVE_TTL_HOURS", "DOCKER_AUTO_REMOVE_TTL_HOURS"),
                    ("DOCKER_PRINT_LOG", "DOCKER_PRINT_LOG"),
                    ("OBJECT_REMOVAL_TTL_HOURS", "OBJECT_REMOVAL_TTL_HOURS"),
                    ("RUNNER_DEFAULT_DOCKER_IMAGE", "RUNNER_DEFAULT_DOCKER_IMAGE"),
                    ("RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME", "RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME"),
                    ("RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD", "RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD"),
                ],
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="setting",
            name="value",
            field=django_cryptography.fields.encrypt(models.TextField(blank=True, default="")),
        ),
    ]