from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.transaction import on_commit
from django.utils import timezone

from config.celery_app import app as celery_app

from core.models import AuthorModel, NameDescriptionBaseModel

RUN_STATUS = (
    ("SUBMITTED", "SUBMITTED"),
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("FAILED", "FAILED"),
)

# If STATUS_MAPPING is updated, also update the mapping in run/views/run.py (annotated field 'status_external')
STATUS_MAPPING = {
    "SUBMITTED": "queued",
    "PENDING": "queued",
    "PAUSED": "paused",
    "IN_PROGRESS": "running",
    "SUCCESS": "finished",
    "COMPLETED": "finished",
    "FAILED": "failed",
}


def get_status_external(status: str) -> str:
    """Translate a status used in Run model to status used external

    Args:
        status (str): status used in Run model

    Returns:
        str: status used external
    """
    return STATUS_MAPPING[status]


class RunQuerySet(models.QuerySet):
    def active(self, add_select_related: bool = False):
        active_query = self.filter(
            deleted_at__isnull=True,
            jobdef__deleted_at__isnull=True,
            jobdef__project__deleted_at__isnull=True,
            jobdef__project__workspace__deleted_at__isnull=True,
            package__deleted_at__isnull=True,
        )

        if add_select_related is True:
            active_query = active_query.select_related(
                "jobdef__project__workspace",
                "created_by_member__avatar_file",
                "created_by_member__user__avatar_file",
                "payload",
                "package__package_file",
                "result",
                "output",
                "run_image",
            ).prefetch_related(
                "artifacts__artifact_file",
                "metrics_meta",
                "variables_meta",
            )

        return active_query


class Run(AuthorModel, NameDescriptionBaseModel):
    name = models.CharField(max_length=255, blank=True, null=False, default="", db_index=True)

    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE)
    payload = models.ForeignKey("job.JobPayload", on_delete=models.CASCADE, blank=True, null=True)
    package = models.ForeignKey("package.Package", on_delete=models.CASCADE, null=True)
    result = models.OneToOneField("storage.File", null=True, on_delete=models.CASCADE, related_name="run_result_file")

    status = models.CharField(max_length=20, choices=RUN_STATUS, default="SUBMITTED")

    trigger = models.CharField(max_length=20, blank=True, default="API")

    # Register the start and end of a run
    started_at = models.DateTimeField(null=True, editable=False)
    finished_at = models.DateTimeField(null=True, editable=False)
    duration = models.PositiveIntegerField(
        null=True, blank=True, editable=False, help_text="Duration of the run in seconds"
    )

    environment_name = models.CharField(max_length=256, default="")
    timezone = models.CharField(max_length=256, default="UTC")
    run_image = models.ForeignKey("job.RunImage", on_delete=models.CASCADE, null=True)

    celery_task_id = models.CharField(max_length=120, blank=True, help_text="The task ID of the Celery run")

    objects = RunQuerySet().as_manager()

    permission_by_action = {
        "list": "project.run.list",
        (
            "retrieve",
            "log",
            "manifest",
            "status",
            "storage_file_download",
        ): "project.run.view",
        (
            "create",
            "result",
            "artifact",
            "storage_file_upload_part",
            "storage_file_upload_complete",
            "storage_file_upload_abort",
        ): "project.run.create",
        "partial_update": "project.run.edit",
        "destroy": "project.run.remove",
    }

    @property
    def project(self):
        return self.jobdef.project

    @property
    def workspace(self):
        return self.jobdef.project.workspace

    @property
    def upload_directory(self):
        return "runs/" + self.suuid[:2].lower() + "/" + self.suuid[2:4].lower() + "/" + self.suuid

    @property
    def upload_result_directory(self):
        return self.upload_directory + "/result"

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
        self.save(
            update_fields=[
                "status",
                "modified_at",
            ]
        )

    def set_finished_at(self):
        self.finished_at = timezone.now()
        if self.started_at:
            self.duration = (self.finished_at - self.started_at).seconds
        self.save(
            update_fields=[
                "duration",
                "finished_at",
                "modified_at",
            ]
        )

        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_run_notification",
                kwargs={"run_uuid": self.uuid},
            )
        )

    def to_pending(self):
        self.set_status("PENDING")

        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_run_notification",
                kwargs={"run_uuid": self.uuid},
            )
        )

    def to_failed(self, exit_code=1):
        self.output.save_stdout()
        self.output.save_exitcode(exit_code=exit_code)
        self.set_finished_at()
        self.set_status("FAILED")

    def to_completed(self):
        self.output.save_stdout()
        self.set_finished_at()
        self.set_status("COMPLETED")

    def to_inprogress(self):
        self.started_at = timezone.now()
        self.save(
            update_fields=[
                "started_at",
                "modified_at",
            ]
        )
        self.set_status("IN_PROGRESS")

    def set_run_image(self, run_image):
        self.run_image = run_image
        self.save(
            update_fields=[
                "run_image",
                "modified_at",
            ]
        )

    def set_timezone(self, run_timezone):
        self.timezone = run_timezone
        self.save(
            update_fields=[
                "timezone",
                "modified_at",
            ]
        )

    def get_result(self):
        try:
            result = self.result
        except ObjectDoesNotExist:
            return None
        return result

    def get_status_external(self) -> str:
        return get_status_external(self.status)

    def get_duration(self) -> int:
        if self.is_finished and self.duration:
            return self.duration
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).seconds
        if self.started_at:
            return (timezone.now() - self.started_at).seconds
        return 0

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
