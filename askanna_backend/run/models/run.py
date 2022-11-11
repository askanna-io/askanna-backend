from core.models import AuthorModel, BaseModel
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.fields import DateTimeField
from django.db.transaction import on_commit
from django.utils import timezone

from config.celery_app import app as celery_app

RUN_STATUS = (
    ("SUBMITTED", "SUBMITTED"),
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("FAILED", "FAILED"),
)


class Run(AuthorModel, BaseModel):
    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, to_field="uuid")
    payload = models.ForeignKey("job.JobPayload", on_delete=models.CASCADE, blank=True, null=True)
    package = models.ForeignKey("package.Package", on_delete=models.CASCADE, null=True)

    # Clarification, jobid holds the job-id of Celery
    jobid = models.CharField(max_length=120, blank=True, null=True, help_text="The job-id of the Celery run")
    status = models.CharField(max_length=20, choices=RUN_STATUS)

    trigger = models.CharField(max_length=20, blank=True, null=True, default="API")

    member = models.ForeignKey("users.Membership", on_delete=models.CASCADE, null=True)

    # Register the start and end of a run
    started = DateTimeField(null=True, editable=False)
    finished = DateTimeField(null=True, editable=False)
    duration = models.PositiveIntegerField(
        null=True, blank=True, editable=False, help_text="Duration of the run in seconds"
    )

    environment_name = models.CharField(max_length=256, default="")
    timezone = models.CharField(max_length=256, default="UTC")

    # the image where it was ran with
    run_image = models.ForeignKey("job.RunImage", on_delete=models.CASCADE, null=True)

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

        # fire off a Celery tasks to notify the user
        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_run_notification",
                args=None,
                kwargs={"run_uuid": self.uuid},
            )
        )

    def to_pending(self):
        self.set_status("PENDING")

        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_run_notification",
                args=None,
                kwargs={"run_uuid": self.uuid},
            )
        )

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

    def get_result(self):
        try:
            result = self.result
        except ObjectDoesNotExist:
            return None
        return result

    def get_name(self):
        """
        Return the name for short-serialisation
        """
        return None or self.name

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "run",
            "suuid": self.suuid,
            "name": self.get_name(),
        }

    class Meta:
        ordering = ["-created"]
