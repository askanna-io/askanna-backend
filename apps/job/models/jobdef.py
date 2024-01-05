from django.db import models
from django.db.models import Q

from core.models import NameDescriptionBaseModel
from core.utils.config import get_setting


class JobQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted_at__isnull=True,
            project__deleted_at__isnull=True,
            project__workspace__deleted_at__isnull=True,
        )

    def inactive(self):
        return self.filter(
            Q(deleted_at__isnull=False)
            | Q(project__deleted_at__isnull=False)
            | Q(project__workspace__deleted_at__isnull=False)
        )


class JobManager(models.Manager):
    def get_queryset(self):
        return JobQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class JobDef(NameDescriptionBaseModel):
    name = models.CharField(max_length=255, blank=False, null=False, db_index=True)

    environment_image = models.CharField(max_length=2048, blank=True, editable=False)
    timezone = models.CharField(max_length=256, default="UTC")

    project = models.ForeignKey("project.Project", on_delete=models.CASCADE, blank=True, null=True)

    objects = JobManager()

    permission_by_action = {
        "list": "project.job.list",
        "retrieve": "project.job.view",
        "destroy": "project.job.remove",
        "partial_update": "project.job.edit",
        "new_run": "project.run.create",
    }

    @property
    def workspace(self):
        return self.project.workspace

    def __str__(self):
        return f"{self.name} ({self.suuid})"

    def get_environment_image(self) -> str:
        """Return the environment image set for this job definition or if not set the default runner image"""
        return self.environment_image or get_setting(name="RUNNER_DEFAULT_DOCKER_IMAGE")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Job definition"
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
