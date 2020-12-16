from rest_framework import serializers

from flow.models import FlowDef


class FlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowDef
        fields = (
            'id',
            'uuid',
            'name',
        )
