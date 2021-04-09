# -*- coding: utf-8 -*-
from django.db import models
from encrypted_model_fields.fields import EncryptedTextField

from core.models import SlimBaseModel


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
    value = EncryptedTextField(max_length=4096, blank=True)
    is_masked = models.BooleanField(default=False)

    def get_value(self, show_masked=False):
        if self.is_masked and not show_masked:
            return "***masked***"
        return self.value

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Variable"
        verbose_name_plural = "Job Variables"
