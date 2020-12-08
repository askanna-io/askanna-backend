from django.db import models
from users.models import User
import uuid

from core.models import SlimBaseModel

class ChunkedArtifactPart(SlimBaseModel):
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this artifactchunk")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    artifact = models.ForeignKey('job.JobArtifact', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ["-created"]
