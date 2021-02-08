# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.serializers import BaseArchiveDetailSerializer
from job.models import (
    JobDef,
    JobRun,
    JobPayload,
    JobArtifact,
    ChunkedArtifactPart,
    ChunkedJobOutputPart,
    JobOutput,
    JobVariable,
    RunMetrics,
)
from project.models import Project


class JobOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOutput
        fields = "__all__"


class JobSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        return str(instance.project.uuid)

    class Meta:
        model = JobDef
        fields = "__all__"


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
    trigger = serializers.SerializerMethodField("get_user")
    runner = serializers.SerializerMethodField("get_runner")
    jobid = serializers.SerializerMethodField("get_jobid")

    payload = serializers.SerializerMethodField("get_payload")

    jobdef = serializers.SerializerMethodField("get_jobdef")

    metrics = serializers.SerializerMethodField("get_metrics")

    def get_metrics(self, instance):
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

    def get_jobid(self, instance):
        # FIXME: this is to fix empty jobids from unran Celery jobs
        return instance.jobid

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
        has_artifact = instance.artifact.exists()
        if has_artifact:
            artifact = instance.artifact.first()
            return artifact.relation_to_json
        return {"relation": "artifact", "name": None, "uuid": None, "short_uuid": None}

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
                return instance.member.relation_to_json
            return instance.owner.relation_to_json
        return {
            "relation": "user",
            "name": None,
            "uuid": None,
            "short_uuid": None,
        }

    class Meta:
        model = JobRun
        exclude = ["member"]


class JobArtifactSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField("get_project")
    # jobrun = serializers.SerializerMethodField('get_jobrun')

    def get_project(self, instance):
        project = instance.jobrun.jobdef.project
        return project.relation_to_json

    def get_jobrun(self, instance):
        jobrun = instance.jobrun
        return jobrun.relation_to_json

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


class ChunkedJobOutputPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedJobOutputPart
        fields = "__all__"


class JobVariableCreateSerializer(serializers.ModelSerializer):
    project = serializers.CharField(max_length=19)
    value = serializers.CharField(trim_whitespace=False, allow_blank=True)

    def validate_project(self, value):
        project = value
        # is it a short_uuid?
        # or is it a uuid?
        try:
            dbproject = Project.objects.get(short_uuid=project)
        except ObjectDoesNotExist:
            dbproject = Project.objects.get(uuid=project)

        # return uuid for this project
        return dbproject

    def create(self, validated_data):
        instance = JobVariable.objects.create(**validated_data)
        return instance

    def validate_value(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("A value cannot be empty.")
        return value

    def to_representation(self, instance):
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.name,
            "value": instance.value,
            "is_masked": instance.is_masked,
            "project": instance.project.relation_to_json,
            "created": instance.created,
            "modified": instance.modified,
        }

    class Meta:
        model = JobVariable
        exclude = [
            "deleted",
        ]


class JobVariableSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField("get_project")
    value = serializers.SerializerMethodField("get_value")

    def get_value(self, instance):
        """
            return masked value by default
        """
        show_masked = self.context["request"].query_params.get("show_masked")
        if instance.is_masked and not show_masked:
            return "***masked***"
        return instance.value

    def get_project(self, instance):
        """
            return short project relation info
        """
        return instance.project.relation_to_json

    class Meta:
        model = JobVariable
        exclude = [
            "deleted",
        ]


class JobVariableUpdateSerializer(serializers.ModelSerializer):
    value = serializers.CharField(trim_whitespace=False, allow_blank=True)

    class Meta:
        model = JobVariable
        fields = ["name", "value", "is_masked"]

    def validate_value(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("A value cannot be empty.")
        return value

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.value = validated_data.get("value", instance.value)
        instance.is_masked = validated_data.get("is_masked", instance.is_masked)
        instance.save()
        return instance

    def to_representation(self, instance):
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.name,
            "value": instance.value,
            "is_masked": instance.is_masked,
            "project": instance.project.relation_to_json,
            "created": instance.created,
            "modified": instance.modified,
        }


class RunMetricsSerializer(serializers.ModelSerializer):
    """Serializer for RunMetrics model.
    At this moment we take in as-is, no futher validation etc.
    """

    def to_representation(self, instance):
        # print(self.context["request"].query_params)
        """
        This is used in 'list' views
        """
        ordering = self.context.get("request").query_params.get("ordering", [])
        if ordering == "-metric.name":
            return instance.get_sorted(reverse=True)
        return instance.metrics

    class Meta:
        model = RunMetrics
        fields = ["uuid", "short_uuid", "metrics"]
        read_only_fields = ["uuid", "short_uuid"]

