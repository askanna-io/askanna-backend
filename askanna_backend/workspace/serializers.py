# -*- coding: utf-8 -*-
from rest_framework import serializers

from workspace.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    is_member = serializers.SerializerMethodField("get_is_member")

    def get_is_member(self, instance):
        return instance.is_member

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.visibility = validated_data.get("visibility", instance.visibility)
        instance.save()
        instance.refresh_from_db()
        return instance

    def validate_visibility(self, value):
        if value.upper() not in ["PRIVATE", "PUBLIC"]:
            raise serializers.ValidationError(
                f"`visibility` can only be PUBLIC or PRIVATE, not {value}"
            )
        return value.upper()

    class Meta:
        model = Workspace
        fields = (
            "uuid",
            "short_uuid",
            "name",
            "description",
            "visibility",
            "created",
            "modified",
            "is_member",
        )
