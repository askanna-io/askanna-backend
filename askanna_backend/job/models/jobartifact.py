# -*- coding: utf-8 -*-
import os

from django.db import models
from django.conf import settings

from core.models import SlimBaseModel


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
            self.jobrun.uuid.hex,
        )

    def __str__(self):
        return str(self.uuid)

    @property
    def stored_path(self):
        return os.path.join(
            settings.ARTIFACTS_ROOT, self.storage_location, self.filename
        )

    @property
    def filename(self):
        return "artifact_{}.zip".format(self.uuid.hex)

    @property
    def read(self):
        """
            Read the artifact from filesystem and return as Zip
        """

        with open(self.stored_path, "rb") as f:
            return f.read()

    def write(self, stream):
        """
            Write contents to the filesystem
        """
        os.makedirs(
            os.path.join(settings.ARTIFACTS_ROOT, self.storage_location), exist_ok=True
        )
        with open(self.stored_path, "wb") as f:
            f.write(stream.read())

    def prune(self):
        os.remove(self.stored_path)

    def get_name(self):
        return self.filename

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
