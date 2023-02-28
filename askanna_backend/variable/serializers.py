from project.models import Project
from project.serializers import ProjectRelationSerializer
from rest_framework import serializers
from variable.models import Variable
from workspace.serializers import WorkspaceRelationSerializer


class VariableSerializer(serializers.ModelSerializer):
    value = serializers.CharField(
        source="get_value", default=None, trim_whitespace=False, allow_blank=True, required=False
    )
    project = ProjectRelationSerializer(read_only=True)
    workspace = WorkspaceRelationSerializer(read_only=True, source="project.workspace")

    def validate_is_masked(self, value):
        if self.instance and self.instance.is_masked is True and value is False:
            raise serializers.ValidationError("Cannot unmask a masked variable")
        return value

    def update(self, instance, validated_data):
        if validated_data.get("get_value"):
            validated_data["value"] = validated_data.pop("get_value")
        instance = super().update(instance, validated_data)
        if instance.is_masked:
            instance.value = "***masked***"
        return instance

    class Meta:
        model = Variable
        fields = [
            "suuid",
            "name",
            "value",
            "is_masked",
            "project",
            "workspace",
            "created_at",
            "modified_at",
        ]


class VariableCreateSerializer(VariableSerializer):
    project_suuid = serializers.SlugRelatedField(
        slug_field="suuid",
        write_only=True,
        required=True,
        queryset=Project.objects.active(),
        source="project",
    )
    value = serializers.CharField(default=None, trim_whitespace=False, allow_blank=True, required=False)
    is_masked = serializers.BooleanField(default=False, required=False)

    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.is_masked:
            instance.value = "***masked***"
        return instance

    class Meta(VariableSerializer.Meta):
        fields = VariableSerializer.Meta.fields + ["project_suuid"]
