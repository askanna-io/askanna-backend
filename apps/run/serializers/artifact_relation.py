from rest_framework import serializers

from run.models import RunArtifact


class ArtifactRelationSerializer(serializers.ModelSerializer):
    relation = serializers.CharField(read_only=True, default="artifact")
    suuid = serializers.CharField(read_only=True)
    size = serializers.IntegerField(read_only=True, source="artifact_file.size")
    count_dir = serializers.IntegerField(read_only=True, source="artifact_file.count_dir_from_zipfile")
    count_files = serializers.IntegerField(read_only=True, source="artifact_file.count_files_from_zipfile")

    class Meta:
        model = RunArtifact
        fields = [
            "relation",
            "suuid",
            "size",
            "count_dir",
            "count_files",
        ]
