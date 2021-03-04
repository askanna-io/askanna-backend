# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from job.models import (
    JobDef,
    JobRun,
    JobPayload,
)

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


class JobPayloadSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        return instance.jobdef.project.relation_to_json

    class Meta:
        model = JobPayload
        fields = "__all__"


class JobRunSerializer(serializers.ModelSerializer):
    artifact = serializers.SerializerMethodField("get_artifact")
    package = serializers.SerializerMethodField("get_package")
    version = serializers.SerializerMethodField("get_version")
    project = serializers.SerializerMethodField("get_project")
    owner = serializers.SerializerMethodField("get_user")
    trigger = serializers.SerializerMethodField("get_trigger")
    runner = serializers.SerializerMethodField("get_runner")

    payload = serializers.SerializerMethodField("get_payload")

    jobdef = serializers.SerializerMethodField("get_jobdef")

    metricsmeta = serializers.SerializerMethodField("get_metricsmeta")

    def get_metricsmeta(self, instance):
        try:
            metrics = instance.metrics.get()
        except ObjectDoesNotExist:
            return {
                "count": 0,
                "size": 0,
                "labels": [],
                "keys": [],
            }
        return {
            "count": metrics.count,
            "size": metrics.size,
            "labels": instance.metric_labels,
            "keys": instance.metric_keys,
        }

    def get_payload(self, instance):
        payload = JobPayloadSerializer(instance.payload, many=False)
        return payload.data

    def get_jobdef(self, instance):
        jobdef = instance.jobdef
        return jobdef.relation_to_json

    def get_runner(self, instance):
        # FIXME: replace with actual values
        return {
            "name": "Python 3.7",
            "uuid": "",
            "short_uuid": "1234-5678-9012-3456",
            "cpu_time": (instance.modified - instance.created).seconds,
            "cpu_cores": 1,
            "memory_mib": 70,
            "job_status": 0,
        }

    def get_trigger(self, instance):
        # FIXME: return the real trigger source
        return "API"

    def get_version(self, instance):
        # FIXME: replace with actual version information
        # stick version to the package version
        return {
            "relation": "version",
            "name": "latest",
            "uuid": "",
            "short_uuid": "2222-3333-2222-2222",
        }

    def get_artifact(self, instance):
        try:
            artifact = instance.artifact.first()
            assert artifact is not None, "No artifact"
        except AssertionError:
            return {
                "relation": "artifact",
                "name": None,
                "uuid": None,
                "short_uuid": None,
            }
        else:
            return artifact.relation_to_json

    def get_package(self, instance):
        package = instance.package
        if package:
            return package.relation_to_json
        return {
            "relation": "package",
            "name": "latest",
            "uuid": None,
            "short_uuid": None,
        }

    def get_project(self, instance):
        project = instance.jobdef.project
        return project.relation_to_json

    def get_user(self, instance):
        if instance.owner:
            if instance.member:
                return instance.member.relation_to_json_with_avatar
            return instance.owner.relation_to_json
        return {
            "relation": "user",
            "name": None,
            "uuid": None,
            "short_uuid": None,
        }

    class Meta:
        model = JobRun
        exclude = [
            "jobid",
            "member",
            "metric_keys",
            "metric_labels",
        ]
