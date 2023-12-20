from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from account.serializers.membership import MembershipRelationSerializer
from core.serializers import RelationSerializer
from job.serializers import JobPayloadRelationSerializer, RunImageRelationSerializer
from run.models import Run
from run.serializers.artifact_relation import ArtifactRelationSerializer
from run.serializers.log import LogRelationSerializer
from run.serializers.result import ResultRelationSerializer


class EnvironmentSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    image = RunImageRelationSerializer()
    timezone = serializers.CharField(read_only=True)


class NameTypeSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)


class NameTypeCountSerializer(NameTypeSerializer):
    count = serializers.IntegerField(read_only=True)


class MetricsMetaSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True, default=0)
    size = serializers.IntegerField(read_only=True, default=0)
    metric_names = NameTypeCountSerializer(many=True)
    label_names = NameTypeSerializer(many=True)


class VariablesMetaSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True, default=0)
    size = serializers.IntegerField(read_only=True, default=0)
    variable_names = NameTypeCountSerializer(many=True)
    label_names = NameTypeSerializer(many=True)


class RunSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True, source="get_status_external")
    duration = serializers.IntegerField(read_only=True, source="get_duration")
    trigger = serializers.CharField(read_only=True)

    created_by = MembershipRelationSerializer(read_only=True, source="created_by_member")

    package = RelationSerializer(read_only=True)
    payload = JobPayloadRelationSerializer(read_only=True)

    result = ResultRelationSerializer(read_only=True)
    artifact = serializers.SerializerMethodField()
    metrics_meta = serializers.SerializerMethodField()
    variables_meta = serializers.SerializerMethodField()
    log = LogRelationSerializer(read_only=True, source="output")

    environment = serializers.SerializerMethodField()

    job = RelationSerializer(read_only=True, source="jobdef")
    project = RelationSerializer(read_only=True, source="jobdef.project")
    workspace = RelationSerializer(read_only=True, source="jobdef.project.workspace")

    @extend_schema_field(MetricsMetaSerializer)
    def get_metrics_meta(self, instance):
        try:
            metrics_meta = instance.metrics_meta.get()
        except ObjectDoesNotExist:
            metrics_meta_data = {
                "count": 0,
                "size": 0,
                "metric_names": [],
                "label_names": [],
            }
        else:
            metrics_meta_data = {
                "count": metrics_meta.count,
                "size": metrics_meta.size,
                "metric_names": metrics_meta.metric_names or [],
                "label_names": metrics_meta.label_names or [],
            }

        return MetricsMetaSerializer(metrics_meta_data).data

    @extend_schema_field(VariablesMetaSerializer)
    def get_variables_meta(self, instance):
        try:
            variables_meta = instance.variables_meta.get()
        except ObjectDoesNotExist:
            run_variables_meta = {
                "count": 0,
                "size": 0,
                "variable_names": [],
                "label_names": [],
            }
        else:
            # For the frontend we make sure that if labels 'source' and/or 'is_masked' are in the label_names
            # dictionary, that we add them as the first label in the list.
            label_names = []
            if variables_meta.label_names:
                label_names = list(filter(lambda x: x["name"] != "is_masked", variables_meta.label_names))
                if len(label_names) != len(variables_meta.label_names):
                    label_names = [{"name": "is_masked", "type": "tag"}] + label_names
                label_names = list(filter(lambda x: x["name"] != "source", label_names))
                if len(label_names) != len(variables_meta.label_names):
                    label_names = [{"name": "source", "type": "string"}] + label_names

            run_variables_meta = {
                "count": variables_meta.count,
                "size": variables_meta.size,
                "variable_names": variables_meta.variable_names or [],
                "label_names": label_names,
            }

        return VariablesMetaSerializer(run_variables_meta).data

    @extend_schema_field(EnvironmentSerializer)
    def get_environment(self, instance):
        environment = {
            "name": instance.environment_name,
            "image": instance.run_image,
            "timezone": instance.timezone,
        }
        return EnvironmentSerializer(environment).data

    @extend_schema_field(ArtifactRelationSerializer)
    def get_artifact(self, instance):
        try:
            artifact = instance.artifact.first()
        except (AttributeError, ObjectDoesNotExist):
            pass
        else:
            if artifact:
                return ArtifactRelationSerializer(artifact).data

        return None

    class Meta:
        model = Run
        fields = [
            "suuid",
            "name",
            "description",
            "status",
            "started_at",
            "finished_at",
            "duration",
            "trigger",
            "created_by",
            "package",
            "payload",
            "result",
            "artifact",
            "metrics_meta",
            "variables_meta",
            "log",
            "environment",
            "job",
            "project",
            "workspace",
            "created_at",
            "modified_at",
        ]


class RunStatusSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True, source="get_status_external")
    duration = serializers.IntegerField(read_only=True, source="get_duration")
    created_by = MembershipRelationSerializer(read_only=True, source="created_by_member")
    job = RelationSerializer(read_only=True, source="jobdef")
    project = RelationSerializer(read_only=True, source="jobdef.project")
    workspace = RelationSerializer(read_only=True, source="jobdef.project.workspace")
    next_url = serializers.SerializerMethodField(allow_null=True)

    @extend_schema_field(OpenApiTypes.URI)
    def get_next_url(self, instance):
        request = self.context["request"]
        url_base = f"{request.scheme}://{request.META['HTTP_HOST']}/v1/run/{instance.suuid}/"

        if instance.is_finished:
            try:
                if instance.result:
                    return url_base + "result/"
            except ObjectDoesNotExist:
                return None

        return url_base + "status/"

    class Meta:
        model = Run
        fields = [
            "suuid",
            "status",
            "name",
            "started_at",
            "finished_at",
            "duration",
            "next_url",
            "created_by",
            "job",
            "project",
            "workspace",
            "created_at",
            "modified_at",
        ]
