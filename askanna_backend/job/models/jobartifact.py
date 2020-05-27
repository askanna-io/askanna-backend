# -*- coding: utf-8 -*-
import json
import os
import uuid

from django.db import models
from django.conf import settings

from core.models import BaseModel, SlimBaseModel


class JobArtifact(SlimBaseModel):
    """
    Output of a JobRun stored into an archive
    """
    jobrun = models.ForeignKey(
        "job.JobRun", on_delete=models.CASCADE, to_field="uuid", related_name="artifact"
    )

    size = models.PositiveIntegerField(editable=False, default=0)

    @property
    def storage_location(self):
        return os.path.join(
            self.jobrun.jobdef.project.uuid.hex,
            self.jobrun.jobdef.uuid.hex,
            self.jobrun.uuid.hex
        )

    def __str__(self):
        return str(self.uuid)

    @property
    def filename(self):
        return "artifact_{}.zip".format(self.uuid.hex)

    @property
    def read(self):
        """
            Read the artifact from filesystem and return as Zip
        """

        store_path = [
            settings.ARTIFACTS_ROOT, 
            self.storage_location, 
            self.filename
        ]

        with open(os.path.join(*store_path), "rb") as f:
            return f.read()

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Artifact"
        verbose_name_plural = "Job Artifacts"
