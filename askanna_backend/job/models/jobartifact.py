# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.db import models

from core.models import SlimBaseModel, ArtifactModelMixin


class JobArtifact(ArtifactModelMixin, SlimBaseModel):
    """
    Output of a JobRun stored into an archive
    """

    filetype = "artifact"
    filextension = "zip"
    filereadmode = "rb"
    filewritemode = "wb"

    def get_storage_location(self):
        return os.path.join(
            self.jobrun.jobdef.project.uuid.hex,
            self.jobrun.jobdef.uuid.hex,
            self.jobrun.uuid.hex,
        )

    def get_base_path(self):
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location)

    def get_full_path(self):
        return os.path.join(
            settings.ARTIFACTS_ROOT, self.storage_location, self.filename
        )

    jobrun = models.ForeignKey(
        "job.JobRun", on_delete=models.CASCADE, to_field="uuid", related_name="artifact"
    )

    size = models.PositiveIntegerField(editable=False, default=0)

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "artifact",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Artifact"
        verbose_name_plural = "Job Artifacts"
