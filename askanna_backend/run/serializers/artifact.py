from core.serializers import BaseArchiveDetailSerializer
from rest_framework import serializers
from run.models import (
    ChunkedRunArtifactPart,
    ChunkedRunResultPart,
    RunArtifact,
    RunResult,
)


class RunArtifactSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField("get_workspace")
    project = serializers.SerializerMethodField("get_project")
    job = serializers.SerializerMethodField("get_job")
    run = serializers.SerializerMethodField("get_run")

    def get_workspace(self, instance):
        return instance.run.jobdef.project.workspace.relation_to_json

    def get_project(self, instance):
        return instance.run.jobdef.project.relation_to_json

    def get_job(self, instance):
        return instance.run.jobdef.relation_to_json

    def get_run(self, instance):
        return instance.run.relation_to_json

    class Meta:
        model = RunArtifact
        fields = [
            "suuid",
            "workspace",
            "project",
            "job",
            "run",
            "size",
            "count_dir",
            "count_files",
            "created",
            "modified",
        ]


class RunArtifactSerializerDetail(RunArtifactSerializer, BaseArchiveDetailSerializer):
    class Meta:
        model = RunArtifact
        fields = [
            "suuid",
            "workspace",
            "project",
            "job",
            "run",
            "size",
            "count_dir",
            "count_files",
            "cdn_base_url",
            "created",
            "modified",
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


class RunResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunResult
        exclude = [
            "uuid",
            "deleted",
        ]


class ChunkedRunResultPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunResultPart
        fields = "__all__"
