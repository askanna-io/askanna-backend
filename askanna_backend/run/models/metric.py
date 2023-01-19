import io
import json
import os

from core.models import ArtifactModelMixin, SlimBaseModel
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone
from run.utils import get_unique_names_with_data_type


class RunMetricMeta(ArtifactModelMixin, SlimBaseModel):
    """Store metrics for a Run"""

    filetype = "runmetrics"
    filextension = "json"
    filereadmode = "r"
    filewritemode = "w"

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

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="metrics_meta")

    @property
    def metrics(self):
        return self.load_from_file()

    @metrics.setter
    def metrics(self, value):
        self.write(io.StringIO(json.dumps(value)))

    count = models.PositiveIntegerField(editable=False, default=0, help_text="Count of metrics")
    size = models.PositiveIntegerField(editable=False, default=0, help_text="File size of metrics JSON")

    metric_names = models.JSONField(
        blank=True,
        null=True,
        editable=False,
        default=None,
        help_text="Unique metric names and data type for metric",
    )
    label_names = models.JSONField(
        blank=True,
        null=True,
        editable=False,
        default=None,
        help_text="Unique metric label names and data type for metric label",
    )

    # suuid is taken from the parent Run model.
    @property
    def suuid(self):
        """Return the suuid from the parent Run instance."""
        return self.run.suuid

    def load_from_file(self, reverse=False):
        with open(self.stored_path, "r") as f:
            return json.loads(f.read())

    def prune(self):
        super().prune()

        # also remove the rows of metrics attached to this object
        RunMetricRow.objects.filter(run__suuid=self.suuid).delete()

    def update_meta(self):
        """
        Update the meta information metric_names and label_names
        """
        run_metrics = RunMetricRow.objects.filter(run__suuid=self.suuid)
        if not run_metrics:
            return

        def compose_response(instance, metric):
            var = {
                "run_suuid": instance.suuid,
                "metric": metric.metric,
                "label": metric.label,
                "created": metric.created.isoformat(),
            }
            return var

        self.count = len(run_metrics)
        self.size = len(json.dumps([compose_response(self, v) for v in run_metrics]).encode("utf-8"))

        all_metric_names = []
        all_label_names = []
        for metric in run_metrics:
            all_metric_names.append(
                {
                    "name": metric.metric.get("name"),
                    "type": metric.metric.get("type"),
                    "count": 1,
                }
            )

            labels = metric.label
            if labels:
                for label in labels:
                    all_label_names.append(
                        {
                            "name": label.get("name"),
                            "type": label.get("type"),
                        }
                    )

        unique_metric_names = None
        if all_metric_names:
            unique_metric_names = get_unique_names_with_data_type(all_metric_names)
        self.metric_names = unique_metric_names

        unique_label_names = None
        if all_label_names:
            unique_label_names = get_unique_names_with_data_type(all_label_names)
        self.label_names = unique_label_names

        self.save(update_fields=["count", "size", "metric_names", "label_names"])

    class Meta:
        db_table = "run_metric_meta"
        ordering = ["-created"]


# TODO: Rename to RunMetric after release v0.21.0
class RunMetricRow(SlimBaseModel):
    """
    Tracked Metrics of a Run
    """

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="metrics")

    # We keep hard references to the project/job/run suuid because historically this model had no hard relations
    # to the other database models
    project_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    job_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    run_suuid = models.CharField(max_length=32, db_index=True, editable=False)

    metric = models.JSONField(
        editable=False,
        default=None,
        help_text="JSON field as list with multiple objects which are metrics, but we limit to one",
    )
    label = models.JSONField(
        editable=False,
        default=None,
        help_text="JSON field as list with multiple objects which are labels",
    )

    # Redefine the created field, we want this to be overwritabe and with other default
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "run_metric_row"
        ordering = ["-created"]
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
