from django.db import transaction
from rest_framework import serializers

from config import celery_app

from core.serializers import FlexibleField, LabelSerializer
from run.models import Run, RunMetric


class RunMetricObjectSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    value = FlexibleField(required=True)
    type = serializers.CharField(required=True)


class RunMetricSerializer(serializers.ModelSerializer):
    run_suuid = serializers.CharField(source="run.suuid", required=True)
    metric = RunMetricObjectSerializer(required=True)
    label = serializers.ListField(child=LabelSerializer(), required=False, allow_null=True)
    created_at = serializers.DateTimeField(required=True)

    class Meta:
        model = RunMetric
        fields = [
            "run_suuid",
            "metric",
            "label",
            "created_at",
        ]


class RunMetricUpdateSerializer(serializers.Serializer):
    metrics = serializers.ListField(child=RunMetricSerializer(), required=True, write_only=True)

    def update(self):
        assert hasattr(self, "_errors"), "You must call `.is_valid()` before calling `.update()`."
        assert not self.errors, "You cannot call `.update()` on a serializer with invalid data."

        for metric in self.validated_data["metrics"]:
            RunMetric.objects.get_or_create(
                run=self.instance,
                metric=metric["metric"],
                label=metric["label"] if metric["label"] is not [] else None,
                created_at=metric["created_at"],
            )

        transaction.on_commit(
            lambda: celery_app.send_task(
                "run.tasks.update_run_metrics_file_and_meta",
                kwargs={"run_suuid": self.instance.suuid},
            )
        )

    class Meta:
        model = Run
