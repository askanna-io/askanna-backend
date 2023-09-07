from django.db import models
from django_cryptography.fields import encrypt

from .base import BaseModel


class Setting(BaseModel):
    AVAILABLE_SETTINGS = [
        ("ASKANNA_UI_URL", "ASKANNA_UI_URL"),
        ("DEFAULT_FROM_EMAIL", "DEFAULT_FROM_EMAIL"),
        ("DOCKER_AUTO_REMOVE_TTL_HOURS", "DOCKER_AUTO_REMOVE_TTL_HOURS"),
        ("DOCKER_PRINT_LOG", "DOCKER_PRINT_LOG"),
        ("MINIO_SETTINGS", "MINIO_SETTINGS"),
        ("OBJECT_REMOVAL_TTL_HOURS", "OBJECT_REMOVAL_TTL_HOURS"),
        ("RUNNER_DEFAULT_DOCKER_IMAGE", "RUNNER_DEFAULT_DOCKER_IMAGE"),
        ("RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME", "RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME"),
        ("RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD", "RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD"),
    ]

    name = models.CharField(unique=True, choices=AVAILABLE_SETTINGS, max_length=150)
    value = encrypt(models.TextField(blank=True, null=False, default=""))
