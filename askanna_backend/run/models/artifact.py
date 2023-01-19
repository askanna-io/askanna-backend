import os

from core.models import ArtifactModelMixin, SlimBaseModel
from django.conf import settings
from django.db import models


class RunArtifact(ArtifactModelMixin, SlimBaseModel):
    """
    Artifact of a run stored into an archive file
    """

    filetype = "artifact"
    filextension = "zip"
    filereadmode = "rb"
    filewritemode = "wb"

    def get_storage_location(self):
        return os.path.join(
            self.run.jobdef.project.uuid.hex,
            self.run.jobdef.uuid.hex,
            self.run.uuid.hex,
        )

    def get_base_path(self):
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location)

    def get_full_path(self):
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location, self.filename)

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="artifact")

    size = models.PositiveIntegerField(editable=False, default=0)
    count_dir = models.PositiveIntegerField(editable=False, default=0)
    count_files = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        db_table = "run_artifact"
        ordering = ["-created"]


class ChunkedRunArtifactPart(SlimBaseModel):
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this artifactchunk")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    artifact = models.ForeignKey("RunArtifact", on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Run artifact chunk"
        verbose_name_plural = "Run artifacts chunks"
