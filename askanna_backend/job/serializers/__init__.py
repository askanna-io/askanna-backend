# -*- coding: utf-8 -*-
from rest_framework import serializers

from job.models import JobDef

from .artifact import (  # noqa: F401
    JobArtifactSerializer,
    JobArtifactSerializerDetail,
    JobArtifactSerializerForInsert,
    ChunkedArtifactPartSerializer,
    JobOutputSerializer,
    ChunkedJobOutputPartSerializer,
)
from .metric import RunMetricsRowSerializer, RunMetricsSerializer  # noqa: F401
from .variable import (  # noqa: F401
    JobVariableCreateSerializer,
    JobVariableUpdateSerializer,
    JobVariableSerializer,
)
from .runvariable import (  # noqa: F401
    RunVariableRowSerializer,
    RunVariablesSerializer,
)
from .run import JobRunSerializer, JobPayloadSerializer  # noqa: F401


class JobSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField("get_project")
    environment = serializers.SerializerMethodField("get_environment")

    def get_project(self, instance):
        return instance.project.relation_to_json

    def get_environment(self, instance):
        # FIXME: this is for backwards compatibility, must be removed once workers are in place
        return "python3.7"

    class Meta:
        model = JobDef
        exclude = (
            "title",
            "deleted",
        )


class StartJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = "__all__"
