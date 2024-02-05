import json

from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone

from config import celery_app

from core.models import AuthorModel, NameDescriptionBaseModel
from run.redis import RedisRunLogQueue

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
                "log_file",
                "payload_file",
                "package__package_file",
                "result_file",
                "run_image",
                "metrics_file",
                "variables_file",
            ).prefetch_related(
                "artifacts__artifact_file",
            )

        return active_query


class Run(AuthorModel, NameDescriptionBaseModel):
    name = models.CharField(max_length=255, blank=True, null=False, default="", db_index=True)

    trigger = models.CharField(max_length=20, blank=True, default="API")
    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE)
    package = models.ForeignKey("package.Package", on_delete=models.CASCADE, null=True)
    payload_file = models.OneToOneField(
        "storage.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="run_payload_file",
        help_text="File with the run payload in JSON format",
    )

    status = models.CharField(max_length=20, choices=RUN_STATUS, default="SUBMITTED")
    exit_code = models.IntegerField(null=True, default=None)
    log_file = models.OneToOneField(
        "storage.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="run_log_file",
        help_text="File with the run log in JSON format",
    )

    result_file = models.OneToOneField(
        "storage.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="run_result_file",
        help_text="File with the run result",
    )

    metrics_file = models.OneToOneField(
        "storage.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="run_metrics_file",
        help_text="File with the run metrics in JSON format",
    )
    metrics_meta = models.JSONField(
        null=True,
        editable=False,
        default=None,
        help_text="Meta information about run metrics",
    )

    variables_file = models.OneToOneField(
        "storage.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="run_variables_file",
        help_text="File with the run variables in JSON format",
    )
    variables_meta = models.JSONField(
        null=True,
        editable=False,
        default=None,
        help_text="Meta information about run variables",
    )

    started_at = models.DateTimeField(null=True, editable=False)
    finished_at = models.DateTimeField(null=True, editable=False)
    duration = models.PositiveIntegerField(
        null=True, blank=True, editable=False, help_text="Duration of the run in seconds"
    )

    environment_name = models.CharField(max_length=256, default="")
    timezone = models.CharField(max_length=256, default="UTC")
    run_image = models.ForeignKey("job.RunImage", on_delete=models.CASCADE, null=True)

    # TODO: remove archive_job_payload field after release v0.29.0
    archive_job_payload = models.ForeignKey("job.JobPayload", on_delete=models.CASCADE, blank=True, null=True)

    objects = RunQuerySet().as_manager()

    permission_by_action = {
        "list": "project.run.list",
        (
            "retrieve",
            "log",
            "status",
            "storage_file_info",
            "storage_file_download",
            "metric_list",
            "variable_list",
        ): "project.run.view",
        (
            "create",
            "manifest",
            "result",
            "artifact",
            "storage_file_upload_part",
            "storage_file_upload_complete",
            "storage_file_upload_abort",
        ): "project.run.create",
        (
            "partial_update",
            "metric_update",
            "variable_update",
        ): "project.run.edit",
        "destroy": "project.run.remove",
    }

    _log_queue = None

    @property
    def job(self):
        return self.jobdef

    @property
    def project(self):
        return self.job.project

    @property
    def workspace(self):
        return self.job.project.workspace

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

    @property
    def log_queue(self) -> RedisRunLogQueue:
        if self._log_queue is None:
            self._log_queue = RedisRunLogQueue(self)

        return self._log_queue

    @log_queue.setter
    def log_queue(self, value) -> RedisRunLogQueue | None:
        self._log_queue = value

    def set_status(self, status_code: str) -> None:
        self.status = status_code
        self.save(
            update_fields=[
                "status",
                "modified_at",
            ]
        )

    def set_exit_code(self, exit_code: int = 0) -> None:
        self.exit_code = exit_code
        self.save(
            update_fields=[
                "exit_code",
                "modified_at",
            ]
        )

    def set_finished_at(self) -> None:
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

        transaction.on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_run_notification",
                kwargs={"run_suuid": self.suuid},
            )
        )

    def to_pending(self) -> None:
        self.set_status("PENDING")

        transaction.on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_run_notification",
                kwargs={"run_suuid": self.suuid},
            )
        )

    def to_inprogress(self) -> None:
        self.started_at = timezone.now()
        self.save(
            update_fields=[
                "started_at",
                "modified_at",
            ]
        )
        self.set_status("IN_PROGRESS")

    def to_completed(self) -> None:
        self.save_log(force=True, remove_log_queue=True)
        self.set_finished_at()
        self.set_status("COMPLETED")
        self.set_exit_code(exit_code=0)

    def to_failed(self, exit_code: int = 1) -> None:
        self.save_log(force=True, remove_log_queue=True)
        self.set_finished_at()
        self.set_status("FAILED")
        self.set_exit_code(exit_code=exit_code)

    def set_run_image(self, run_image) -> None:
        self.run_image = run_image
        self.save(
            update_fields=[
                "run_image",
                "modified_at",
            ]
        )

    def set_timezone(self, run_timezone) -> None:
        self.timezone = run_timezone
        self.save(
            update_fields=[
                "timezone",
                "modified_at",
            ]
        )

    def get_log(self) -> list:
        if self.is_finished:
            cache_key = f"run.Run:log:{self.suuid}"
            log = cache.get(cache_key, [])
            if not log and self.log_file:
                with self.log_file.file.open() as log_file:
                    log = json.load(log_file)
                cache.set(cache_key, log)
        else:
            log = self.log_queue.get()

        return log

    def get_log_size(self) -> int:
        if self.log_file:
            return self.log_file.file.size
        return len(json.dumps(self.get_log()).encode())

    def get_log_lines(self) -> int:
        return len(self.get_log())

    def add_to_log(self, message: str, timestamp: str | None = None, print_log: bool = False) -> None:
        """
        Add a message to the run log queue and trigger a task to save the log to a file. The latest is done every
        5 seconds to prevent too many write actions to the file storage.

        Args:
            message (str): The message to add to the log.
            timestamp (str | None): The timestamp of the message. Defaults to None and in that case the current
                datetime is used.
            print_log (bool): Whether to print the log. Defaults to False.
        """
        self.log_queue.add(message=message, timestamp=timestamp, print_log=print_log)

        if (
            not hasattr(self, "log_queue_last_save")
            or not self.log_queue_last_save
            or (timezone.now() - self.log_queue_last_save).seconds > 5
        ):
            self.log_queue_last_save = timezone.now()
            celery_app.send_task(
                "run.tasks.save_run_log",
                kwargs={"run_suuid": self.suuid},
            )

    def save_log(self, force: bool = False, remove_log_queue: bool = False) -> None:
        """
        Save the run log to a file and optionally remove the log queue.

        Args:
            force (bool): Whether to force the writing to a file. Defaults to False.
            remove_log_queue (bool): Whether to remove the log queue. Defaults to False.
        """
        self.log_queue.write_to_file(force)

        if remove_log_queue:
            self.log_queue.remove()
            self.log_queue = None

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

    def __str__(self) -> str:
        if self.name:
            return f"Run: {self.name} ({self.suuid})"
        return f"Run: {self.suuid}"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
