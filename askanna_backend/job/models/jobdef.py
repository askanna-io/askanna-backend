# -*- coding: utf-8 -*-
from django.db import models

from core.models import BaseModel


class JobDef(BaseModel):
    """
    Consider this as the job registry storing the identity of the job itself.

    FIXME:
        - the job name cannot be unique, since this would be across our system,
          different clients are very likely to use the same name, and this
          should be fine. The uniqueness is based on the uuid.
    """

    name = models.CharField(max_length=50)
    project = models.ForeignKey(
        "project.Project", on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.name

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
