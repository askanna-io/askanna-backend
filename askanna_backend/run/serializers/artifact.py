from core.serializers import BaseArchiveDetailSerializer
from job.serializers import JobRelationSerializer
from project.serializers import ProjectRelationSerializer
from rest_framework import serializers
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
            "created",
            "modified",
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
            "created",
            "modified",
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
            "created",
        ]


class ChunkedRunArtifactPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunArtifactPart
        fields = "__all__"
