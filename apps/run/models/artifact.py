from pathlib import Path

from django.conf import settings
from django.db import models

from core.models import BaseModel, FileBaseModel


class RunArtifact(FileBaseModel):
    """
    Artifact of a run stored into an archive file
    """

    file_type = "artifact"
    file_extension = "zip"
    file_readmode = "rb"
    file_writemode = "wb"

    def get_storage_location(self) -> Path:
        return Path(self.run.jobdef.project.uuid.hex) / self.run.jobdef.uuid.hex / self.run.uuid.hex

    def get_root_location(self) -> Path:
        return settings.ARTIFACTS_ROOT

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="artifact")

    size = models.PositiveIntegerField(editable=False, default=0)
    count_dir = models.PositiveIntegerField(editable=False, default=0)
    count_files = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        db_table = "run_artifact"
        ordering = ["-created_at"]


class ChunkedRunArtifactPart(BaseModel):
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this artifactchunk")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    artifact = models.ForeignKey("RunArtifact", on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Run artifact chunk"
        verbose_name_plural = "Run artifacts chunks"
