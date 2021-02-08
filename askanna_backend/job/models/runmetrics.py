# -*- coding: utf-8 -*-
"""Define the model that stores the metrics for a job run."""
import os
from django.conf import settings
from django.db import models

from core.fields import JSONField
from core.models import SlimBaseModel, ArtifactModelMixin


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
        return os.path.join(
            settings.ARTIFACTS_ROOT, self.storage_location, self.filename
        )

    jobrun = models.ForeignKey(
        "job.JobRun", on_delete=models.CASCADE, to_field="uuid", related_name="metrics"
    )
    metrics = JSONField(blank=True, null=True)

    count = models.PositiveIntegerField(editable=False, default=0)
    size = models.PositiveIntegerField(editable=False, default=0)

    filtered_metrics = {}
    applied_filters = []

    # short_uuid is taken from the parent JobRun model.
    @property
    def short_uuid(self):
        """Return the short_uuid from the parent JobRun instance."""
        return self.jobrun.short_uuid

    @property
    def stored_path_reversed_sort(self):
        return os.path.join(
            settings.ARTIFACTS_ROOT, self.storage_location, self.filename_reversed_sort
        )

    @property
    def filename_reversed_sort(self):
        return "metrics_reversed_{}.json".format(self.jobrun.uuid.hex)

    def load_metrics_from_file(self, reverse=False):
        path = reverse and self.stored_path_reversed_sort or self.stored_path
        with open(path, "r") as f:
            return f.read()

    def get_sorted(self, reverse=False) -> dict:
        """
        Load sorted metrics from filesystem,
        """
        return self.load_metrics_from_file(reverse=reverse)

    # def apply_filter(self, filter_cond: [] = None) -> dict:
    #     if not self.applied_filters:
    #         self.filtered_metrics = self.metrics.copy()

    #     self.applied_filters.append(filter_cond)
    #     # apply the filter condition
    #     filter_scope, filter_key, filter_operation, filter_value = filter_cond

    #     for metric in self.filtered_metrics:
    #         # select scope to check (metric or label)
    #         scoped_search = metric[filter_scope]
    #         # find filter_key and do match
    #         hit = scoped_search.get(filter_key)
    #         filtered_in = []
    #         if hit:
    #             # for now only to equal comparison
    #             if hit == filter_value:
    #                 # we include this metric
    #                 filtered_in.append(hit)
    #             else:
    #                 pass

    #     return self

    class Meta:
        """Options for RunMetrics."""

        ordering = ["-created"]
        verbose_name = "Run Metrics"
        verbose_name_plural = "Run Metrics"
