from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class RunVariableQuerySet(models.QuerySet):
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


class RunVariable(BaseModel):
    """
    Tracked Variables of a Run
    """

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="variables")

    variable = models.JSONField(
        editable=False,
        help_text="JSON field to store a variable",
    )
    is_masked = models.BooleanField(default=False)
    label = models.JSONField(
        null=True,
        default=None,
        editable=False,
        help_text="JSON field as list with multiple objects which are labels",
    )

    # Redefine the created_at field, we want this to be overwritable
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    objects = RunVariableQuerySet.as_manager()

    class Meta:
        db_table = "run_variable"
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
