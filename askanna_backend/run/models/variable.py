import io
import json
import os

from core.models import ArtifactModelMixin, SlimBaseModel
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone
from run.utils import get_unique_names_with_data_type


class RunVariable(ArtifactModelMixin, SlimBaseModel):
    """Store variables for a Run"""

    filetype = "runvariables"
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

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, to_field="uuid", related_name="runvariables")

    @property
    def variables(self):
        return self.load_from_file()

    @variables.setter
    def variables(self, value):
        self.write(io.StringIO(json.dumps(value)))

    count = models.PositiveIntegerField(editable=False, default=0, help_text="Count of variables")
    size = models.PositiveIntegerField(editable=False, default=0, help_text="File size of variables JSON")

    variable_names = models.JSONField(
        blank=True,
        null=True,
        editable=False,
        default=None,
        help_text="Unique variable names and data type for variable",
    )
    label_names = models.JSONField(
        blank=True,
        null=True,
        editable=False,
        default=None,
        help_text="Unique variable label names and data type for variable label",
    )

    # suuid is taken from the parent Run model.
    @property
    def suuid(self):
        """Return the suuid from the parent Run instance."""
        return self.run.suuid

    def load_from_file(self):
        with open(self.stored_path, "r") as f:
            return json.loads(f.read())

    def prune(self):
        super().prune()

        # also remove the rows of variables attached to this object
        RunVariableRow.objects.filter(run_suuid=self.suuid).delete()

    def update_meta(self):
        """
        Update the meta information variable_names and label_names
        """
        runvariables = RunVariableRow.objects.filter(run_suuid=self.suuid)
        if not runvariables:
            return

        def compose_response(instance, variable):
            var = {
                "run_suuid": instance.suuid,
                "variable": variable.variable,
                "label": variable.label,
                "created": variable.created.isoformat(),
            }
            return var

        self.count = len(runvariables)
        self.size = len(json.dumps([compose_response(self, v) for v in runvariables]).encode("utf-8"))

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
        db_table = "run_variable"
        ordering = ["-created"]


class RunVariableRow(SlimBaseModel):
    """
    Tracked Variables of a Run
    """

    # We keep hard references to the project/job/run suuid because this model doesn't have hard relations to the other
    # database models
    #
    # project_suuid and job_suuid should not be exposed
    project_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    job_suuid = models.CharField(max_length=32, db_index=True, editable=False)
    run_suuid = models.CharField(max_length=32, db_index=True, editable=False)

    variable = models.JSONField(
        editable=False,
        default=None,
        help_text="JSON field to store a variable",
    )
    is_masked = models.BooleanField(default=False)
    label = models.JSONField(
        editable=False,
        default=None,
        help_text="JSON field as list with multiple objects which are labels",
    )

    # Redefine the created field, we want this to be overwritabe and with other default
    created = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "run_variablerow"
        ordering = ["-created"]
        verbose_name = "Run variable row"
        verbose_name_plural = "Run variables rows"
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
