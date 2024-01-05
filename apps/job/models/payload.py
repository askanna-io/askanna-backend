from django.db import models

from core.models import BaseModel


# TODO: remove RunResult model after release v0.29.0
class JobPayload(BaseModel):
    """
    Input for a Run
    """

    jobdef = models.ForeignKey("job.JobDef", on_delete=models.CASCADE, related_name="job_payload")

    size = models.PositiveIntegerField(editable=False, default=0)
    lines = models.PositiveIntegerField(editable=False, default=0)
    owner = models.ForeignKey("account.User", on_delete=models.SET_NULL, null=True)

    class Meta:
        get_latest_by = "created_at"
        ordering = ["-created_at"]
