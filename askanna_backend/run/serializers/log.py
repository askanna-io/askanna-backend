from rest_framework import serializers
from run.models import RunLog


class LogRelationSerializer(serializers.ModelSerializer):
    relation = serializers.CharField(read_only=True, default="log")
    suuid = serializers.ReadOnlyField()
    name = serializers.CharField(read_only=True, default="log.json")
    size = serializers.IntegerField(read_only=True)
    lines = serializers.IntegerField(read_only=True)

    class Meta:
        model = RunLog
        fields = [
            "relation",
            "suuid",
            "name",
            "size",
            "lines",
        ]
