from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from account.serializers.membership import MembershipRelationSerializer
from core.serializers import RelationSerializer
from job.serializers import RunImageRelationSerializer
from run.models import Run
from run.serializers.artifact import ArtifactRelationSerializer
from run.serializers.log import LogRelationSerializer
from storage.serializers import FileDownloadInfoSerializer


class EnvironmentSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    image = RunImageRelationSerializer(read_only=True)
    timezone = serializers.CharField(read_only=True)


class NameTypeSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)


class NameTypeCountSerializer(NameTypeSerializer):
    count = serializers.IntegerField(read_only=True)


class FileSerializer(serializers.Serializer):
    filename = serializers.CharField(read_only=True, source="name")
    size = serializers.IntegerField(read_only=True)
    etag = serializers.CharField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    download_info = FileDownloadInfoSerializer(read_only=True, source="*")


class MetricsMetaSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True, default=0, source="metrics_meta.count")
    size = serializers.IntegerField(read_only=True, default=0, source="metrics_file.size")
    metric_names = NameTypeCountSerializer(many=True, read_only=True, source="metrics_meta.metric_names")
    label_names = NameTypeSerializer(many=True, read_only=True, source="metrics_meta.label_names")
    download_info = FileDownloadInfoSerializer(read_only=True, source="metrics_file")


class VariablesMetaSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True, default=0, source="variables_meta.count")
    size = serializers.IntegerField(read_only=True, default=0, source="variables_file.size")
    variable_names = NameTypeCountSerializer(many=True, read_only=True, source="variables_meta.variable_names")
    label_names = NameTypeSerializer(many=True, read_only=True, source="variables_meta.label_names")
    download_info = FileDownloadInfoSerializer(read_only=True, source="variables_file")


class RunSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)

    name = serializers.CharField()
    description = serializers.CharField()

    status = serializers.CharField(read_only=True, source="get_status_external")
    started_at = serializers.DateTimeField(read_only=True)
    finished_at = serializers.DateTimeField(read_only=True)
    duration = serializers.IntegerField(read_only=True, source="get_duration")

    trigger = serializers.CharField(read_only=True)

    created_by = MembershipRelationSerializer(read_only=True, source="created_by_member")

    package = RelationSerializer(read_only=True)
    payload = FileSerializer(read_only=True)

    result = FileSerializer(read_only=True)
    artifact = ArtifactRelationSerializer(read_only=True, many=True, source="artifacts")
    metrics_meta = MetricsMetaSerializer(source="*")
    variables_meta = VariablesMetaSerializer(source="*")
    log = LogRelationSerializer(read_only=True, source="output")

    environment = serializers.SerializerMethodField()

    job = RelationSerializer(read_only=True, source="jobdef")
    project = RelationSerializer(read_only=True, source="jobdef.project")
    workspace = RelationSerializer(read_only=True, source="jobdef.project.workspace")

    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    @extend_schema_field(EnvironmentSerializer)
    def get_environment(self, instance):
        environment = {
            "name": instance.environment_name,
            "image": instance.run_image,
            "timezone": instance.timezone,
        }
        return EnvironmentSerializer(environment).data

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
    suuid = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True, source="get_status_external")
    started_at = serializers.DateTimeField(read_only=True)
    finished_at = serializers.DateTimeField(read_only=True)
    duration = serializers.IntegerField(read_only=True, source="get_duration")

    class Meta:
        model = Run
        fields = [
            "suuid",
            "status",
            "started_at",
            "finished_at",
            "duration",
        ]
