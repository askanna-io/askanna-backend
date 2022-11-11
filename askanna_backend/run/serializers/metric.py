from rest_framework import serializers
from run.models import RunMetric, RunMetricRow


class RunMetricSerializer(serializers.ModelSerializer):
    """Serializer for RunMetric model.
    At this moment we take in as-is, no futher validation etc.
    """

    def to_representation(self, instance):
        metrics = instance.metrics
        return metrics

    class Meta:
        model = RunMetric
        fields = ["uuid", "suuid", "metrics"]
        read_only_fields = ["uuid", "suuid"]


class RunMetricRowSerializer(serializers.ModelSerializer):
    """Serializer for RunMetricRow model."""

    class Meta:
        model = RunMetricRow
        fields = ["run_suuid", "metric", "label", "created"]
        read_only_fields = ["run_suuid"]
