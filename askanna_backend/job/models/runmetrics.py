"""Define the model that stores the metrics for a job run."""
from django.db import models

from core.fields import JSONField
from core.models import SlimBaseModel


class RunMetrics(SlimBaseModel):
    """Store metrics for a JobRun."""

    jobrun = models.ForeignKey(
        "job.JobRun", on_delete=models.CASCADE, to_field="uuid", related_name="metrics"
    )
    metrics = JSONField(blank=True, null=True)

    count = models.PositiveIntegerField(editable=False, default=0)
    size = models.PositiveIntegerField(editable=False, default=0)

    # short_uuid is taken from the parent JobRun model.
    @property
    def short_uuid(self):
        """Return the short_uuid from the parent JobRun instance."""
        return self.jobrun.short_uuid

    class Meta:
        """Options for RunMetrics."""

        ordering = ["-created"]
        verbose_name = "Run Metrics"
        verbose_name_plural = "Run Metrics"
