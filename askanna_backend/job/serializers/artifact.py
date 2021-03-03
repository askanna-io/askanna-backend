# -*- coding: utf-8 -*-
from rest_framework import serializers

from core.serializers import BaseArchiveDetailSerializer
from job.models import JobArtifact, JobOutput, ChunkedArtifactPart, ChunkedJobOutputPart


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


class JobOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOutput
        fields = "__all__"


class ChunkedJobOutputPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedJobOutputPart
        fields = "__all__"

