from django.db import transaction
from rest_framework import serializers

from config import celery_app

from core.serializers import FlexibleField, LabelSerializer
from run.models import Run, RunVariable


class RunVariableObjectSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    value = FlexibleField(required=True)
    type = serializers.CharField(required=True)


class RunVariableSerializer(serializers.ModelSerializer):
    run_suuid = serializers.CharField(source="run.suuid", required=True)
    variable = RunVariableObjectSerializer(required=True)
    label = serializers.ListField(child=LabelSerializer(), required=False, allow_null=True)
    created_at = serializers.DateTimeField(required=True)

    class Meta:
        model = RunVariable
        fields = [
            "run_suuid",
            "variable",
            "label",
            "created_at",
        ]


class RunVariableUpdateSerializer(serializers.Serializer):
    variables = serializers.ListField(child=RunVariableSerializer(), required=True, write_only=True)

    def update(self):
        assert hasattr(self, "_errors"), "You must call `.is_valid()` before calling `.update()`."
        assert not self.errors, "You cannot call `.update()` on a serializer with invalid data."

        for variable in self.validated_data["variables"]:
            RunVariable.objects.get_or_create(
                run=self.instance,
                variable=variable["variable"],
                label=variable["label"] if variable["label"] is not [] else None,
                created_at=variable["created_at"],
            )

        transaction.on_commit(
            lambda: celery_app.send_task(
                "run.tasks.update_run_variables_file_and_meta",
                kwargs={"run_suuid": self.instance.suuid},
            )
        )

    class Meta:
        model = Run
