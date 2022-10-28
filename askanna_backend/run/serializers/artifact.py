from core.serializers import BaseArchiveDetailSerializer
from rest_framework import serializers
from run.models import (
    ChunkedRunArtifactPart,
    ChunkedRunResultPart,
    RunArtifact,
    RunResult,
)


class RunArtifactSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        project = instance.run.jobdef.project
        return project.relation_to_json

    class Meta:
        model = RunArtifact
        fields = "__all__"


class RunArtifactSerializerForInsert(serializers.ModelSerializer):
    class Meta:
        model = RunArtifact
        fields = "__all__"


class RunArtifactSerializerDetail(BaseArchiveDetailSerializer):
    class Meta:
        model = RunArtifact
        fields = "__all__"


class ChunkedRunArtifactPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunArtifactPart
        fields = "__all__"


class RunResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunResult
        fields = "__all__"


class ChunkedRunResultPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunResultPart
        fields = "__all__"
