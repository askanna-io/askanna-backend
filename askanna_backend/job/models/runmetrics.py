# -*- coding: utf-8 -*-
import io
import json
import os

from core.models import ArtifactModelMixin, SlimBaseModel
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone
from job.utils import get_unique_names_with_data_type


class RunMetrics(ArtifactModelMixin, SlimBaseModel):
    """Store metrics for a JobRun."""

    filetype = "runmetrics"
    filextension = "json"
    filereadmode = "r"
    filewritemode = "w"

    def get_storage_location(self):
        return os.path.join(
            self.jobrun.jobdef.project.uuid.hex,
            self.jobrun.jobdef.uuid.hex,
            self.jobrun.uuid.hex,
        )

    def get_base_path(self):
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location)

    def get_full_path(self):
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location, self.filename)

    jobrun = models.ForeignKey("job.JobRun", on_delete=models.CASCADE, to_field="uuid", related_name="metrics")

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

    # short_uuid is taken from the parent JobRun model.
    @property
    def short_uuid(self):
        """Return the short_uuid from the parent JobRun instance."""
        return self.jobrun.short_uuid

    def load_from_file(self, reverse=False):
        with open(self.stored_path, "r") as f:
            return json.loads(f.read())

    def prune(self):
        super().prune()

        # also remove the rows of metrics attached to this object
        RunMetricsRow.objects.filter(run_suuid=self.short_uuid).delete()

    def update_meta(self):
        """
        Update the meta information metric_names and label_names
        """
        runmetrics = RunMetricsRow.objects.filter(run_suuid=self.short_uuid)
        if not runmetrics:
            return

        def compose_response(instance, metric):
            var = {
                "run_suuid": instance.short_uuid,
                "metric": metric.metric,
                "label": metric.label,
                "created": metric.created.isoformat(),
            }
            return var

        self.count = len(runmetrics)
        self.size = len(json.dumps([compose_response(self, v) for v in runmetrics]).encode("utf-8"))

        all_metric_names = []
        all_label_names = []
        for metric in runmetrics:
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

        unique_metric_names = get_unique_names_with_data_type(all_metric_names)
        self.metric_names = unique_metric_names

        unique_label_names = None
        if all_label_names:
            unique_label_names = get_unique_names_with_data_type(all_label_names)
        self.label_names = unique_label_names

        self.save(update_fields=["count", "size", "metric_names", "label_names"])

    class Meta:
        ordering = ["-created"]
        verbose_name = "Run Metric"
        verbose_name_plural = "Run Metrics"


class RunMetricsRow(SlimBaseModel):
    """
    Tracked Metrics of a JobRun
    """

    # We keep hard references to the project/job/run suuid because this model doesn't have hard relations to the other
    # database models
    #
    # project_suuid and job_suuid should not be exposed
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
        ordering = ["-created"]
        verbose_name = "Run Metrics Row"
        verbose_name_plural = "Run Metrics Rows"
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
