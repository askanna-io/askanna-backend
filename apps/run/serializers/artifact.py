from rest_framework import serializers

from core.serializers import BaseArchiveDetailSerializer, RelationSerializer
from run.models import ChunkedRunArtifactPart, RunArtifact


class RunArtifactSerializer(serializers.ModelSerializer):
    run = RelationSerializer(read_only=True)
    job = RelationSerializer(read_only=True, source="run.jobdef")
    project = RelationSerializer(read_only=True, source="run.jobdef.project")
    workspace = RelationSerializer(read_only=True, source="run.jobdef.project.workspace")

    class Meta:
        model = RunArtifact
        fields = [
            "suuid",
            "size",
            "count_dir",
            "count_files",
            "run",
            "job",
            "project",
            "workspace",
            "created_at",
            "modified_at",
        ]


class RunArtifactSerializerDetail(RunArtifactSerializer, BaseArchiveDetailSerializer):
    class Meta:
        model = RunArtifact
        fields = [
            "suuid",
            "size",
            "count_dir",
            "count_files",
            "run",
            "job",
            "project",
            "workspace",
            "created_at",
            "modified_at",
            "cdn_base_url",
            "files",
        ]


class RunArtifactSerializerForInsert(serializers.ModelSerializer):
    class Meta:
        model = RunArtifact
        fields = [
            "suuid",
            "run",
            "size",
            "created_at",
        ]


class ChunkedRunArtifactPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunArtifactPart
        fields = "__all__"
