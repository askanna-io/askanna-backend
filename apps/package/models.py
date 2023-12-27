from django.db import models

from core.config import AskAnnaConfig
from core.models import BaseModel
from job.models import JobDef, ScheduledJob


class PackageQuerySet(models.QuerySet):
    def active(self, add_select_related: bool = False):
        active_query = self.filter(
            deleted_at__isnull=True,
            package_file__deleted_at__isnull=True,
            package_file__completed_at__isnull=False,
            project__deleted_at__isnull=True,
            project__workspace__deleted_at__isnull=True,
        ).select_related("package_file")

        if add_select_related is True:
            return active_query.select_related(
                "project__workspace",
                "package_file___created_by__account_membership__user",
            )

        return active_query


class Package(BaseModel):
    project = models.ForeignKey("project.Project", on_delete=models.CASCADE, related_name="packages")
    package_file = models.OneToOneField(
        "storage.File", null=True, on_delete=models.CASCADE, related_name="package_file"
    )

    # TODO: remove these field after migration 0004_move_package_files_to_storage is applied
    archive_filename = models.CharField(max_length=1000, default="")
    archive_size = models.IntegerField(null=True, default=None, help_text="Size of this package in bytes")
    archive_description = models.TextField(default="", blank=True)
    archive_created_by_user = models.ForeignKey(
        "account.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="packages_archived_created_by_user",
    )
    archive_created_by_member = models.ForeignKey("account.Membership", on_delete=models.CASCADE, null=True)
    archive_finished_at = models.DateTimeField(
        "Finished upload at",
        blank=True,
        auto_now_add=False,
        auto_now=False,
        null=True,
        help_text="Date and time when upload of this package was finished",
        db_index=True,
    )

    objects = PackageQuerySet().as_manager()

    permission_by_action = {
        "list": "project.code.list",
        ("retrieve", "storage_file_info", "storage_file_download"): "project.code.view",
        (
            "create",
            "storage_file_upload_part",
            "storage_file_upload_complete",
            "storage_file_upload_abort",
        ): "project.code.create",
        "partial_update": "project.code.edit",
        "destroy": "project.code.remove",
    }

    @property
    def upload_directory(self):
        return "packages/" + self.suuid[:2].lower() + "/" + self.suuid[2:4].lower() + "/" + self.suuid

    def get_name(self) -> str | None:
        if self.package_file:
            return self.package_file.name
        return None

    def get_askanna_config(self) -> AskAnnaConfig | None:
        """
        Reads the askanna.yml as is and return as AskAnnaConfig or None
        """
        if (
            not self.package_file
            or not self.package_file.file
            or "askanna.yml" not in self.package_file.zipfile_namelist
        ):
            return None

        with self.package_file.get_file_from_zipfile("askanna.yml") as config_file:
            return AskAnnaConfig.from_stream(config_file.read())

    def extract_jobs_from_askanna_config(self):
        """
        If jobs are defined in the askanna config related to this package, then create/update the JobDef and
        ScheduledJob objects.
        """
        askanna_config = self.get_askanna_config()
        if askanna_config is None:
            return

        for _, job in askanna_config.jobs.items():
            job_def, _ = JobDef.objects.get_or_create(name=job.name, project=self.project)

            job_def.environment_image = job.environment.image
            job_def.timezone = job.timezone
            job_def.deleted_at = None
            job_def.save(
                update_fields=[
                    "environment_image",
                    "timezone",
                    "deleted_at",
                    "modified_at",
                ]
            )

            # Check what existing schedules where and store the last_run_at and raw_definition
            existing_schedules = ScheduledJob.objects.filter(job=job_def)
            old_schedules = [
                {"last_run_at": schedule.last_run_at, "raw_definition": schedule.raw_definition}
                for schedule in existing_schedules
            ]

            # Clear existing schedules
            existing_schedules.delete()

            for schedule in job.schedules:
                schedule_def = {
                    "job": job_def,
                    "raw_definition": schedule.raw_definition,
                    "cron_definition": schedule.cron_definition,
                    "cron_timezone": schedule.cron_timezone,
                    "member": self.package_file.created_by,
                }

                # Check if from the old schedules we can find a last_run_at looking at the raw_definition.
                # We assume that the raw_definition is unique for a schedule.
                last_run_at = [
                    old.get("last_run_at")
                    for old in old_schedules
                    if str(old.get("raw_definition")) == str(schedule.raw_definition)
                    and old.get("last_run_at") is not None
                ]
                if len(last_run_at) > 0:
                    schedule_def["last_run_at"] = max(last_run_at)

                scheduled_job = ScheduledJob.objects.create(**schedule_def)
                scheduled_job.update_next()

    class Meta:
        get_latest_by = "created_at"
        ordering = ["-created_at"]
