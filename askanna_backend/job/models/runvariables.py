# -*- coding: utf-8 -*-
import io
import itertools
import json
import os

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex

from core.fields import JSONField
from core.models import SlimBaseModel, ArtifactModelMixin


class RunVariables(ArtifactModelMixin, SlimBaseModel):
    """Store runvariables for a JobRun."""

    filetype = "runvariables"
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
        "job.JobRun",
        on_delete=models.CASCADE,
        to_field="uuid",
        related_name="runvariables",
    )

    @property
    def variables(self):
        return self.load_from_file()

    @variables.setter
    def variables(self, value):
        self.write(io.StringIO(json.dumps(value)))

    count = models.PositiveIntegerField(editable=False, default=0)
    size = models.PositiveIntegerField(editable=False, default=0)

    # short_uuid is taken from the parent JobRun model.
    @property
    def short_uuid(self):
        """Return the short_uuid from the parent JobRun instance."""
        return self.jobrun.short_uuid

    def load_from_file(self):
        path = self.stored_path
        try:
            with open(path, "r") as f:
                return json.loads(f.read())
        except FileExistsError as e:
            raise e

    def prune(self):
        super().prune()

        # also remove the rows of variables attached to this object
        RunVariableRow.objects.filter(run_suuid=self.short_uuid).delete()

    def update_meta(self):
        """
        Update the meta information in model JobRun and this model
        First select how many tracked variables we have
        """
        runvariables = RunVariableRow.objects.filter(run_suuid=self.short_uuid)

        def compose_response(instance, variable):
            var = {
                "run_suuid": instance.short_uuid,
                "variable": variable.variable,
                "label": variable.label,
                "created": instance.created.isoformat(),
            }
            return var

        def get_variable_labels(variable):
            return [label.get("name") for label in variable.label]

        self.count = len(runvariables)
        self.size = len(json.dumps([compose_response(self, v) for v in runvariables]))
        self.save(update_fields=["count", "size"])

        self.jobrun.variable_keys = list(
            set([v.variable.get("name") for v in runvariables])
        )
        self.jobrun.variable_labels = list(
            set(itertools.chain(*[get_variable_labels(v) for v in runvariables]))
            - set(["source"])
        )
        self.jobrun.save(update_fields=["variable_keys", "variable_labels"])

    class Meta:
        """Options for RunVariables."""

        ordering = ["-created"]
        verbose_name = "Run Variables"
        verbose_name_plural = "Run Variables"


class RunVariableRow(SlimBaseModel):
    """
    Tracked Variables of a JobRun
    """

    project_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    job_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    run_suuid = models.CharField(max_length=32, db_index=True, editable=False)

    # Redefine the created field, we want this to be overwritabe and with other default
    created = models.DateTimeField(default=timezone.now, db_index=True)

    is_masked = models.BooleanField(default=False)
    variable = JSONField(help_text="JSON field to store a variable")
    label = JSONField(
        help_text="JSON field as list with multiple objects which are labels"
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = "Run variable row"
        verbose_name_plural = "Run variable rows"

        indexes = [
            GinIndex(
                name="runvariable_var_json_idx",
                fields=["label"],
                opclasses=["jsonb_path_ops"],
            ),
            GinIndex(
                name="runvariable_lbl_json_idx",
                fields=["label"],
                opclasses=["jsonb_path_ops"],
            ),
        ]
