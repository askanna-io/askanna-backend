import io
import json
from pathlib import Path

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from core.models import BaseModel, FileBaseModel
from run.utils import get_unique_names_with_data_type


class RunVariableMeta(FileBaseModel):
    """Store variables for a Run"""

    file_type = "runvariables"
    file_extension = "json"

    def get_storage_location(self) -> Path:
        return Path(self.run.jobdef.project.uuid.hex) / self.run.jobdef.uuid.hex / self.run.uuid.hex

    def get_root_location(self) -> Path:
        return settings.VARIABLE_ROOT

    run = models.OneToOneField("run.Run", on_delete=models.CASCADE, related_name="variables_meta")

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
        with self.stored_path.open() as f:
            return json.loads(f.read())

    def prune(self):
        super().prune()

        # also remove the rows of variables attached to this object
        RunVariableRow.objects.filter(run__suuid=self.suuid).delete()

    def update_meta(self):
        """
        Update the meta information variable_names and label_names
        """
        run_variables = RunVariableRow.objects.filter(run__suuid=self.suuid)
        if not run_variables:
            return

        def compose_response(instance, variable):
            return {
                "run_suuid": instance.suuid,
                "variable": variable.variable,
                "label": variable.label,
                "created_at": variable.created_at.isoformat(),
            }

        self.count = len(run_variables)
        self.size = len(json.dumps([compose_response(self, v) for v in run_variables]).encode("utf-8"))

        all_variable_names = []
        all_label_names = []
        for variable in run_variables:
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

        self.save(
            update_fields=[
                "count",
                "size",
                "variable_names",
                "label_names",
                "modified_at",
            ]
        )

    class Meta:
        db_table = "run_variable_meta"
        ordering = ["-created_at"]


# TODO: Rename to RunVariable after release v0.21.0
class RunVariableRow(BaseModel):
    """
    Tracked Variables of a Run
    """

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="variables")

    # TODO: remove these fields after release v0.21.0
    # We keep hard references to the project/job/run suuid because historically this model had no hard relations
    # to the other database models
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

    # Redefine the created_at field, we want this to be overwritabe and with other default
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "run_variable_row"
        ordering = ["-created_at"]
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
