from rest_framework import serializers
from run.models import RunVariable, RunVariableMeta


class RunVariableUpdateSerializer(serializers.ModelSerializer):
    variables = serializers.ListField(child=serializers.JSONField(), required=True)

    class Meta:
        model = RunVariableMeta
        fields = ["variables"]


class RunVariableSerializer(serializers.ModelSerializer):
    """Serializer for RunVariable model."""

    class Meta:
        model = RunVariable
        fields = ["run_suuid", "variable", "label", "created"]
        read_only_fields = ["run_suuid", "created"]
