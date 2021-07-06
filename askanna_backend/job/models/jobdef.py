# -*- coding: utf-8 -*-
from django.db import models

from core.models import BaseModel


class JobDef(BaseModel):
    """
    Consider this as the job registry storing the identity of the job itself.
    """

    project = models.ForeignKey(
        "project.Project", on_delete=models.CASCADE, blank=True, null=True
    )

    environment_image = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        editable=False,
    )
    timezone = models.CharField(max_length=256, default="UTC")

    def get_name(self):
        return self.name

    @property
    def relation_to_json(self):
        return {
            "relation": "jobdef",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Definition"
        verbose_name_plural = "Job Definitions"
