# -*- coding: utf-8 -*-
import json
import os
import uuid

from django.db import models

from core.models import BaseModel, SlimBaseModel

from job.models.const import JOB_STATUS


class JobRun(BaseModel):
    """
    FIXME:
        - I don't think we need JobRun to have an active relationship to the
          jobpayload. It can be a reference to it. If we need to retrieve
          the payload, we can do so, via the uuid.
        - JobRun should have a 1:1 relationship, since there doesn't seem to
          be any reason where we should have a JobRun withouth a JobOutput.
    """

    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, to_field="uuid")
    payload = models.ForeignKey("job.JobPayload", on_delete=models.CASCADE, null=True)
    package = models.ForeignKey("package.Package", on_delete=models.CASCADE, null=True)

    # Clarification, jobid holds the job-id of Celery
    # Status is also the status from the Celery run
    jobid = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS)

    # stats
    runtime = models.FloatField(default=0)  # FIXME: check with job system
    memory = models.FloatField(default=0)  # FIXME: check with job system

    # FIXME: check time series storage for info on resource usage

    owner = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Run"
        verbose_name_plural = "Job Runs"
