# -*- coding: utf-8 -*-
# from urllib.parse import urlencode
from rest_framework import serializers

from job.models import RunMetrics, RunMetricsRow


class RunMetricsSerializer(serializers.ModelSerializer):
    """Serializer for RunMetrics model.
    At this moment we take in as-is, no futher validation etc.
    """

    def to_representation(self, instance):
        metrics = instance.metrics
        return metrics

    class Meta:
        model = RunMetrics
        fields = ["uuid", "short_uuid", "metrics"]
        read_only_fields = ["uuid", "short_uuid"]


class RunMetricsRowSerializer(serializers.ModelSerializer):
    """Serializer for RunMetricsRow model.
    """

    class Meta:
        model = RunMetricsRow
        fields = ["run_suuid", "metric", "label", "created"]
        read_only_fields = ["run_suuid"]
