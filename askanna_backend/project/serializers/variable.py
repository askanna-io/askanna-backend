from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema_field
from project.models import Project, ProjectVariable
from rest_framework import serializers


class ProjectVariableCreateSerializer(serializers.ModelSerializer):
    project = serializers.CharField(max_length=19)
    value = serializers.CharField(trim_whitespace=False, allow_blank=True)

    def validate_project(self, value):
        try:
            return Project.objects.get(suuid=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Project cannot be found.")

    def create(self, validated_data):
        return ProjectVariable.objects.create(**validated_data)

    def validate_value(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("A value cannot be empty.")
        return value

    def to_representation(self, instance):
        return {
            "suuid": instance.suuid,
            "name": instance.name,
            "value": instance.value,
            "is_masked": instance.is_masked,
            "project": instance.project.relation_to_json,
            "workspace": instance.project.workspace.relation_to_json,
            "created": instance.created,
            "modified": instance.modified,
        }

    class Meta:
        model = ProjectVariable
        exclude = [
            "uuid",
            "deleted",
        ]


class ProjectVariableSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField("get_value")
    project = serializers.SerializerMethodField("get_project")
    workspace = serializers.SerializerMethodField("get_workspace")

    def get_value(self, instance):
        """
        return masked value by default
        """
        show_masked = self.context["request"].query_params.get("show_masked")
        return instance.get_value(show_masked=show_masked)

    @extend_schema_field(
        {"type": "string", "format": "binary", "example": {"relation": "string", "suuid": "string", "name": "string"}}
    )
    def get_project(self, instance):
        return instance.project.relation_to_json

    @extend_schema_field(
        {"type": "string", "format": "binary", "example": {"relation": "string", "suuid": "string", "name": "string"}}
    )
    def get_workspace(self, instance):
        return instance.project.workspace.relation_to_json

    class Meta:
        model = ProjectVariable
        fields = [
            "suuid",
            "name",
            "value",
            "is_masked",
            "project",
            "workspace",
            "created",
            "modified",
        ]


class ProjectVariableUpdateSerializer(serializers.ModelSerializer):
    value = serializers.CharField(trim_whitespace=False, allow_blank=True)

    def validate_value(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("A value cannot be empty.")
        return value

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.value = validated_data.get("value", instance.value)
        instance.is_masked = validated_data.get("is_masked", instance.is_masked)
        instance.save()
        return instance

    def to_representation(self, instance):
        return {
            "suuid": instance.suuid,
            "name": instance.name,
            "value": instance.value,
            "is_masked": instance.is_masked,
            "project": instance.project.relation_to_json,
            "workspace": instance.project.workspace.relation_to_json,
            "created": instance.created,
            "modified": instance.modified,
        }

    class Meta:
        model = ProjectVariable
        fields = [
            "name",
            "value",
            "is_masked",
        ]
