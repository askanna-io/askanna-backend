from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class RunMetricQuerySet(models.QuerySet):
    def active(self, add_select_related: bool = False):
        active_query = self.filter(
            deleted_at__isnull=True,
            run__deleted_at__isnull=True,
            run__jobdef__deleted_at__isnull=True,
            run__jobdef__project__deleted_at__isnull=True,
            run__jobdef__project__workspace__deleted_at__isnull=True,
        )

        if add_select_related is True:
            active_query = active_query.select_related("run")

        return active_query


class RunMetric(BaseModel):
    """
    Tracked Metrics of a Run
    """

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="metrics")

    metric = models.JSONField(
        editable=False,
        help_text="JSON field as list with multiple objects which are metrics, but we limit to one",
    )
    label = models.JSONField(
        null=True,
        default=None,
        editable=False,
        help_text="JSON field as list with multiple objects which are labels",
    )

    # Redefine the created_at field, we want this to be overwritable
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    objects = RunMetricQuerySet.as_manager()

    class Meta:
        db_table = "run_metric"
        ordering = ["-created_at"]
        indexes = [
            GinIndex(
                name="runmetric_metric_json_idx",
                fields=["metric"],
                opclasses=["jsonb_path_ops"],
            ),
            GinIndex(
                name="runmetric_label_json_idx",
                fields=["label"],
                opclasses=["jsonb_path_ops"],
            ),
        ]
