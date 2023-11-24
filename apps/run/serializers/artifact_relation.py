from rest_framework import serializers

from run.models import RunArtifact


class ArtifactRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.CharField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    count_dir = serializers.IntegerField(read_only=True)
    count_files = serializers.IntegerField(read_only=True)

    def get_relation(self, instance) -> str:
        return "artifact"

    class Meta:
        model = RunArtifact
        fields = [
            "relation",
            "suuid",
            "size",
            "count_dir",
            "count_files",
        ]
