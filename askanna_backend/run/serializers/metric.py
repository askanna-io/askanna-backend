from rest_framework import serializers
from run.models import RunMetric, RunMetricMeta


class RunMetricUpdateSerializer(serializers.ModelSerializer):
    metrics = serializers.ListField(child=serializers.JSONField(), required=True)

    class Meta:
        model = RunMetricMeta
        fields = ["metrics"]


class RunMetricSerializer(serializers.ModelSerializer):
    """Serializer for RunMetric model."""

    class Meta:
        model = RunMetric
        fields = ["run_suuid", "metric", "label", "created_at"]
        read_only_fields = ["run_suuid", "created_at"]
