# -*- coding: utf-8 -*-
import json
import os
import uuid

from django.db import models
from django.conf import settings
from encrypted_model_fields.fields import EncryptedTextField


from core.models import BaseModel, SlimBaseModel


class JobVariable(SlimBaseModel):
    """
    Variables for a JobRun
    """

    project = models.ForeignKey(
        "project.Project",
        on_delete=models.CASCADE,
        to_field="uuid",
        related_name="variable",
    )

    name = models.CharField(max_length=128)
    value = EncryptedTextField(max_length=4096)
    is_masked = models.BooleanField(default=False)

    def __str__(self):
        return str(self.uuid)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Variable"
        verbose_name_plural = "Job Variables"
