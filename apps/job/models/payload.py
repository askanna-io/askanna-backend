import json
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q

from core.models import FileBaseModel


class PayloadQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted_at__isnull=True,
            jobdef__deleted_at__isnull=True,
            jobdef__project__deleted_at__isnull=True,
            jobdef__project__workspace__deleted_at__isnull=True,
        )

    def inactive(self):
        return self.filter(
            Q(deleted_at__isnull=False)
            | Q(jobdef__deleted_at__isnull=False)
            | Q(jobdef__project__deleted_at__isnull=False)
            | Q(jobdef__project__workspace__deleted_at__isnull=False)
        )


class PayloadManager(models.Manager):
    def get_queryset(self):
        return PayloadQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class JobPayload(FileBaseModel):
    """
    Input for a Run
    """

    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, related_name="payload")

    objects = PayloadManager()

    @property
    def filename(self) -> str:
        return "payload.json"

    def get_storage_location(self) -> Path:
        return Path(self.jobdef.project.uuid.hex) / self.suuid

    def get_root_location(self) -> Path:
        return settings.PAYLOADS_ROOT

    size = models.PositiveIntegerField(editable=False, default=0)
    lines = models.PositiveIntegerField(editable=False, default=0)
    owner = models.ForeignKey("account.User", on_delete=models.SET_NULL, null=True)

    @property
    def payload(self):
        """
        Read the payload from filesystem and return as JSON object
        """
        return json.loads(self.read)

    class Meta:
        get_latest_by = "created_at"
        ordering = ["-created_at"]
