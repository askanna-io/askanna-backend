# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from job.models import JobVariable
from project.models import Project


class JobVariableCreateSerializer(serializers.ModelSerializer):
    project = serializers.CharField(max_length=19)
    value = serializers.CharField(trim_whitespace=False, allow_blank=True)

    def validate_project(self, value):
        project = value
        # is it a short_uuid?
        # or is it a uuid?
        try:
            dbproject = Project.objects.get(short_uuid=project)
        except ObjectDoesNotExist:
            dbproject = Project.objects.get(uuid=project)

        # return uuid for this project
        return dbproject

    def create(self, validated_data):
        instance = JobVariable.objects.create(**validated_data)
        return instance

    def validate_value(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("A value cannot be empty.")
        return value

    def to_representation(self, instance):
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.name,
            "value": instance.value,
            "is_masked": instance.is_masked,
            "project": instance.project.relation_to_json,
            "created": instance.created,
            "modified": instance.modified,
        }

    class Meta:
        model = JobVariable
        exclude = [
            "deleted",
        ]


class JobVariableSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField("get_project")
    value = serializers.SerializerMethodField("get_value")

    def get_value(self, instance):
        """
        return masked value by default
        """
        show_masked = self.context["request"].query_params.get("show_masked")
        return instance.get_value(show_masked=show_masked)

    def get_project(self, instance):
        """
        return short project relation info
        """
        return instance.project.relation_to_json

    class Meta:
        model = JobVariable
        exclude = [
            "deleted",
        ]


class JobVariableUpdateSerializer(serializers.ModelSerializer):
    value = serializers.CharField(trim_whitespace=False, allow_blank=True)

    class Meta:
        model = JobVariable
        fields = ["name", "value", "is_masked"]

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
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.name,
            "value": instance.value,
            "is_masked": instance.is_masked,
            "project": instance.project.relation_to_json,
            "created": instance.created,
            "modified": instance.modified,
        }
