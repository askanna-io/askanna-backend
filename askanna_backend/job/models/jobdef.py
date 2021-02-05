# -*- coding: utf-8 -*-

from django.db import models

from core.models import BaseModel
from job.models.const import ENV_CHOICES, JOB_BACKENDS


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
    default_payload = models.UUIDField(
        blank=True, null=True, help_text="Default payload to use when not provided"
    )

    function = models.CharField(
        max_length=100, blank=True, null=True, help_text="Function to execute"
    )
    backend = models.CharField(
        max_length=100, choices=JOB_BACKENDS, default="job.celerybackend.CeleryJob"
    )
    visible = models.BooleanField(
        default=True
    )  # FIXME: add rationale and default value

    environment = models.CharField(
        max_length=20, choices=ENV_CHOICES, default="python3.7"
    )

    # FIXME: Should env_variables be in the JobDef, or JobPayload?
    env_variables = models.TextField(blank=True, null=True)

    # FIXME: see what name to use, since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.CharField(max_length=100, blank=True, null=True)

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
