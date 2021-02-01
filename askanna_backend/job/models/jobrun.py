# -*- coding: utf-8 -*-
from django.db import models

from core.fields import ArrayField
from core.models import SlimBaseModel
from job.models.const import JOB_STATUS


class JobRun(SlimBaseModel):
    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, to_field="uuid")
    payload = models.ForeignKey("job.JobPayload", on_delete=models.CASCADE, null=True)
    package = models.ForeignKey("package.Package", on_delete=models.CASCADE, null=True)

    # Clarification, jobid holds the job-id of Celery
    # Status is also the status from the Celery run
    jobid = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS)

    owner = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)
    member = models.ForeignKey("users.Membership", on_delete=models.CASCADE, null=True)

    # The labels field stores what is generated from the metrics
    metric_labels = ArrayField(
        models.CharField(max_length=4096), blank=True, default=list
    )
    # The keys field stores what is generated from the metrics
    metric_keys = ArrayField(
        models.CharField(max_length=8192), blank=True, default=list
    )

    def get_name(self):
        return ""

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "jobrun",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Run"
        verbose_name_plural = "Job Runs"
