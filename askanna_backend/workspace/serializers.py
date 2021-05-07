from rest_framework import serializers

from workspace.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        instance.refresh_from_db()
        return instance

    class Meta:
        model = Workspace
        fields = (
            "uuid",
            "short_uuid",
            "name",
            "description",
            "created",
            "modified",
        )
