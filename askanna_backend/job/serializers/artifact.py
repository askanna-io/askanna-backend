# -*- coding: utf-8 -*-
from rest_framework import serializers

from core.serializers import BaseArchiveDetailSerializer
from job.models import (
    JobArtifact,
    ChunkedArtifactPart,
    RunResult,
    ChunkedRunResultPart,
)


class JobArtifactSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        project = instance.jobrun.jobdef.project
        return project.relation_to_json

    class Meta:
        model = JobArtifact
        fields = "__all__"


class JobArtifactSerializerForInsert(serializers.ModelSerializer):
    class Meta:
        model = JobArtifact
        fields = "__all__"


class JobArtifactSerializerDetail(BaseArchiveDetailSerializer):
    class Meta:
        model = JobArtifact
        fields = "__all__"


class ChunkedArtifactPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedArtifactPart
        fields = "__all__"


class RunResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunResult
        fields = "__all__"


class ChunkedRunResultPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedRunResultPart
        fields = "__all__"
