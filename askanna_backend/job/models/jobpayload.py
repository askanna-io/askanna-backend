# -*- coding: utf-8 -*-
import json
import os
import uuid

from django.db import models
from django.conf import settings

from core.models import BaseModel, SlimBaseModel


class JobPayload(SlimBaseModel):
    """
    Let's assume that we use this to store the payload for a given JobDef.

    Needs to be separare from JobRun, since the same `JobPayload` can be
    used in multiple JobRuns.

    FIXME:
        - check the form and structure of the "payload". We can argue that
          we only need to care of passing a serialized structure to the job.
          The name of this structure is always `payload` and that object
          will need to be deserialized within the job itself if needed.
        - should we create functions here for tinkering with payloads?
          like serialization/deserialization, type checking, etc...
        - set the active flag to reflect on the payload that is set to
          active for the given JobDef.
    """

    jobdef = models.ForeignKey(
        "job.JobDef", on_delete=models.CASCADE, to_field="uuid", related_name="payload"
    )

    @property
    def storage_location(self):
        return os.path.join(self.jobdef.project.uuid.hex, self.short_uuid)

    # FIXME: see what name to use, since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.uuid)

    @property
    def payload(self):
        """
            Read the payload from filesystem and return as JSON object
            # FIXME: in future be in-determined for which filetype
            # FIXME: refactor job system to provide filetype
        """

        store_path = [settings.PAYLOADS_ROOT, self.storage_location, "payload.json"]

        with open(os.path.join(*store_path), "r") as f:
            return json.loads(f.read())

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Payload"
        verbose_name_plural = "Job Payloads"
