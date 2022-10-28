from rest_framework import serializers
from run.models import RunVariable, RunVariableRow


class RunVariableSerializer(serializers.ModelSerializer):
    """Serializer for RunVariables model."""

    def to_representation(self, instance):
        variables = instance.variables
        return variables

    class Meta:
        model = RunVariable
        fields = ["uuid", "short_uuid", "variables"]
        read_only_fields = ["uuid", "short_uuid"]


class RunVariableRowSerializer(serializers.ModelSerializer):
    """Serializer for RunVariableRow model."""

    class Meta:
        model = RunVariableRow
        fields = ["run_suuid", "variable", "label", "created"]
        read_only_fields = ["run_suuid", "label", "created"]
