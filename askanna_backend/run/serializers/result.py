from rest_framework import serializers

from run.models import ChunkedRunResultPart, RunResult


class RunResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunResult
        exclude = [
            "uuid",
            "deleted_at",
        ]


class ChunkedRunResultPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunResultPart
        fields = "__all__"


class ResultRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(default="result.json")
    size = serializers.IntegerField(read_only=True)
    extension = serializers.ReadOnlyField()
    mime_type = serializers.ReadOnlyField()

    def get_relation(self, instance) -> str:
        return "result"

    class Meta:
        model = RunResult
        fields = [
            "relation",
            "suuid",
            "name",
            "size",
            "extension",
            "mime_type",
        ]
