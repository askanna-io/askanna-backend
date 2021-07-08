# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.fields import DateTimeField
from django.utils import timezone

from core.fields import ArrayField
from core.models import BaseModel
from job.models.const import JOB_STATUS


class JobRun(BaseModel):
    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, to_field="uuid")
    payload = models.ForeignKey("job.JobPayload", on_delete=models.CASCADE, null=True)
    package = models.ForeignKey("package.Package", on_delete=models.CASCADE, null=True)

    # Clarification, jobid holds the job-id of Celery
    # Status is also the status from the Celery run
    jobid = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS)

    trigger = models.CharField(max_length=20, blank=True, null=True, default="API")

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

    # The labels field stores what is generated from the tracked_variables
    variable_labels = ArrayField(
        models.CharField(max_length=4096), blank=True, default=list
    )
    # The keys field stores what is generated from the tracked_variables
    variable_keys = ArrayField(
        models.CharField(max_length=8192), blank=True, default=list
    )

    # Register the start and end of a run
    started = DateTimeField(null=True, editable=False)
    finished = DateTimeField(null=True, editable=False)

    environment_name = models.CharField(max_length=256, default="")
    timezone = models.CharField(max_length=256, default="UTC")

    # how long did the run take in seconds?
    duration = models.PositiveIntegerField(null=True, blank=True, editable=False)

    # the image where it was ran with
    run_image = models.ForeignKey("job.RunImage", on_delete=models.SET_NULL, null=True)

    @property
    def is_finished(self):
        """
        We are finished in the following conditions:
        - COMPLETED
        - FAILED
        """
        return self.status in ["COMPLETED", "FAILED"]

    def set_status(self, status_code):
        self.status = status_code
        self.save(update_fields=["status", "modified"])

    def set_finished(self):
        self.finished = timezone.now()
        if self.started:
            self.duration = (self.finished - self.started).seconds
        self.save(update_fields=["duration", "finished", "modified"])

    def to_pending(self):
        self.set_status("PENDING")

    def to_failed(self, exit_code=1):
        self.output.save_stdout()
        self.output.save_exitcode(exit_code=exit_code)
        self.set_finished()
        self.set_status("FAILED")

    def to_completed(self):
        self.output.save_stdout()
        self.set_finished()
        self.set_status("COMPLETED")

    def to_inprogress(self):
        self.started = timezone.now()
        self.save(update_fields=["started"])
        self.set_status("IN_PROGRESS")

    def set_run_image(self, run_image):
        self.run_image = run_image
        self.save(update_fields=["run_image"])

    def set_timezone(self, run_timezone):
        self.timezone = run_timezone
        self.save(update_fields=["timezone"])

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
