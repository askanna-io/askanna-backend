from rest_framework import serializers

from core.serializers import BaseArchiveDetailSerializer
from job.serializers import JobRelationSerializer
from project.serializers import ProjectRelationSerializer
from run.models import ChunkedRunArtifactPart, RunArtifact
from run.serializers.run import RunRelationSerializer
from workspace.serializers import WorkspaceRelationSerializer


class RunArtifactSerializer(serializers.ModelSerializer):
    run = RunRelationSerializer(read_only=True)
    job = JobRelationSerializer(read_only=True, source="run.jobdef")
    project = ProjectRelationSerializer(read_only=True, source="run.jobdef.project")
    workspace = WorkspaceRelationSerializer(read_only=True, source="run.jobdef.project.workspace")

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
