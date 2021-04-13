# -*- coding: utf-8 -*-
import json
import os

from django.db import models
from django.conf import settings

from core.models import SlimBaseModel


class JobPayload(SlimBaseModel):
    """
    Input for a JobRun
    """

    jobdef = models.ForeignKey(
        "job.JobDef", on_delete=models.CASCADE, to_field="uuid", related_name="payload"
    )

    @property
    def stored_path(self):
        return os.path.join(
            settings.PAYLOADS_ROOT, self.storage_location, self.filename
        )

    @property
    def filename(self):
        return "payload.json"

    @property
    def storage_location(self):
        return os.path.join(self.jobdef.project.uuid.hex, self.short_uuid)

    size = models.PositiveIntegerField(editable=False, default=0)
    lines = models.PositiveIntegerField(editable=False, default=0)
    owner = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)

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
        os.makedirs(
            os.path.join(settings.PAYLOADS_ROOT, self.storage_location), exist_ok=True
        )
        with open(self.stored_path, "w") as f:
            f.write(stream.read())

    def prune(self):
        os.remove(self.stored_path)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Payload"
        verbose_name_plural = "Job Payloads"
