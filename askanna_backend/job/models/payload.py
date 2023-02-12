import json
import os

from core.models import SlimBaseModel
from django.conf import settings
from django.db import models
from django.db.models import Q


class PayloadQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted__isnull=True,
            jobdef__deleted__isnull=True,
            jobdef__project__deleted__isnull=True,
            jobdef__project__workspace__deleted__isnull=True,
        )

    def inactive(self):
        return self.filter(
            Q(deleted__isnull=False)
            | Q(jobdef__deleted__isnull=False)
            | Q(jobdef__project__deleted__isnull=False)
            | Q(jobdef__project__workspace__deleted__isnull=False)
        )


class PayloadManager(models.Manager):
    def get_queryset(self):
        return PayloadQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class JobPayload(SlimBaseModel):
    """
    Input for a Run
    """

    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, related_name="payload")

    objects = PayloadManager()

    @property
    def stored_path(self):
        return os.path.join(settings.PAYLOADS_ROOT, self.storage_location, self.filename)

    @property
    def filename(self):
        return "payload.json"

    @property
    def storage_location(self):
        return os.path.join(self.jobdef.project.uuid.hex, self.suuid)

    size = models.PositiveIntegerField(editable=False, default=0)
    lines = models.PositiveIntegerField(editable=False, default=0)
    owner = models.ForeignKey("account.User", on_delete=models.SET_NULL, null=True)

    @property
    def payload(self):
        """
        Read the payload from filesystem and return as JSON object
        # FIXME: in future be in-determined for which filetype
        # FIXME: refactor job system to provide filetype
        """
        return json.loads(self.read)

    @property
    def read(self):
        """
        Read the payload from filesystem and return as JSON object
        """

        with open(self.stored_path, "r") as f:
            return f.read()

    def write(self, stream):
        """
        Write contents to the filesystem
        """
        os.makedirs(os.path.join(settings.PAYLOADS_ROOT, self.storage_location), exist_ok=True)
        with open(self.stored_path, "w") as f:
            f.write(stream.read())

    def prune(self):
        os.remove(self.stored_path)

    class Meta:
        ordering = ["-created"]
