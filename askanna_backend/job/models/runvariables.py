# -*- coding: utf-8 -*-
import io
import json
import os

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from core.models import SlimBaseModel, ArtifactModelMixin
from job.utils import get_unique_names_with_data_type


class RunVariables(ArtifactModelMixin, SlimBaseModel):
    """Store variables for a JobRun."""

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
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location, self.filename)

    jobrun = models.ForeignKey("job.JobRun", on_delete=models.CASCADE, to_field="uuid", related_name="runvariables")

    @property
    def variables(self):
        return self.load_from_file()

    @variables.setter
    def variables(self, value):
        self.write(io.StringIO(json.dumps(value)))

    count = models.PositiveIntegerField(editable=False, default=0, help_text="Count of variables")
    size = models.PositiveIntegerField(editable=False, default=0, help_text="File size of variables JSON")

    variable_names = JSONField(
        blank=True,
        null=True,
        editable=False,
        default=None,
        help_text="Unique variable names and data type for variable",
    )
    label_names = JSONField(
        blank=True,
        null=True,
        editable=False,
        default=None,
        help_text="Unique variable label names and data type for variable label",
    )

    # short_uuid is taken from the parent JobRun model.
    @property
    def short_uuid(self):
        """Return the short_uuid from the parent JobRun instance."""
        return self.jobrun.short_uuid

    def load_from_file(self):
        with open(self.stored_path, "r") as f:
            return json.loads(f.read())

    def prune(self):
        super().prune()

        # also remove the rows of variables attached to this object
        RunVariableRow.objects.filter(run_suuid=self.short_uuid).delete()

    def update_meta(self):
        """
        Update the meta information variable_names and label_names
        """
        runvariables = RunVariableRow.objects.filter(run_suuid=self.short_uuid)
        if not runvariables:
            return

        def compose_response(instance, variable):
            var = {
                "run_suuid": instance.short_uuid,
                "variable": variable.variable,
                "label": variable.label,
                "created": variable.created.isoformat(),
            }
            return var

        self.count = len(runvariables)
        self.size = len(json.dumps([compose_response(self, v) for v in runvariables]))

        all_variable_names = []
        all_label_names = []
        for variable in runvariables:
            all_variable_names.append(
                {
                    "name": variable.variable.get("name"),
                    "type": variable.variable.get("type"),
                    "count": 1,
                }
            )

            labels = variable.label
            if labels:
                for label in labels:
                    all_label_names.append(
                        {
                            "name": label.get("name"),
                            "type": label.get("type"),
                        }
                    )

        unique_variable_names = None
        if all_variable_names:
            unique_variable_names = get_unique_names_with_data_type(all_variable_names)
        self.variable_names = unique_variable_names

        unique_label_names = None
        if all_label_names:
            unique_label_names = get_unique_names_with_data_type(all_label_names)
        self.label_names = unique_label_names

        self.save(update_fields=["count", "size", "variable_names", "label_names"])

    class Meta:
        ordering = ["-created"]
        verbose_name = "Run Variable"
        verbose_name_plural = "Run Variables"


class RunVariableRow(SlimBaseModel):
    """
    Tracked Variables of a JobRun
    """

    # We keep hard references to the project/job/run suuid because this model doesn't have hard relations to the other
    # database models
    #
    # project_suuid and job_suuid should not be exposed
    project_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    job_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    run_suuid = models.CharField(max_length=32, db_index=True, editable=False)

    variable = JSONField(
        editable=False,
        default=None,
        help_text="JSON field to store a variable",
    )
    is_masked = models.BooleanField(default=False)
    label = JSONField(
        editable=False,
        default=None,
        help_text="JSON field as list with multiple objects which are labels",
    )

    # Redefine the created field, we want this to be overwritabe and with other default
    created = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Run Variables Row"
        verbose_name_plural = "Run Variables Rows"
        indexes = [
            GinIndex(
                name="runvariable_variable_json_idx",
                fields=["variable"],
                opclasses=["jsonb_path_ops"],
            ),
            GinIndex(
                name="runvariable_label_json_idx",
                fields=["label"],
                opclasses=["jsonb_path_ops"],
            ),
        ]
