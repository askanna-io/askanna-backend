from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.serializers import RelationSerializer
from job.models import JobDef, JobPayload, RunImage


class ScheduleSerializer(serializers.Serializer):
    raw_definition = serializers.CharField()
    cron_definition = serializers.CharField()
    cron_timezone = serializers.CharField()
    next_run_at = serializers.DateTimeField()
    last_run_at = serializers.DateTimeField()


class NotificationObjectSerializer(serializers.Serializer):
    email = serializers.ListField(default=[], allow_null=True)


class NotificationSerializer(serializers.Serializer):
    all = NotificationObjectSerializer()
    error = NotificationObjectSerializer()


class JobSerializer(serializers.ModelSerializer):
    environment = serializers.CharField(read_only=True, source="get_environment_image")
    timezone = serializers.CharField(read_only=True)
    schedules = serializers.SerializerMethodField("get_schedules", allow_null=True)
    notifications = serializers.SerializerMethodField("get_notifications", allow_null=True)
    project = RelationSerializer(read_only=True)
    workspace = RelationSerializer(read_only=True, source="project.workspace")

    @extend_schema_field(NotificationSerializer)
    def get_notifications(self, instance):
        package = instance.project.packages.first()  # Sorting is handled in the queryset of the View

        if not package:
            return None

        configyml = package.get_askanna_config()
        if configyml is None:
            # we could not parse the config
            return None

        job = configyml.jobs.get(instance.name)
        if job and job.notifications:
            return job.notifications

        return None

    @extend_schema_field(ScheduleSerializer(many=True))
    def get_schedules(self, instance):
        schedules = instance.schedules.all()
        if schedules:
            return [ScheduleSerializer(schedule).data for schedule in schedules]
        return None

    class Meta:
        model = JobDef
        fields = [
            "suuid",
            "name",
            "description",
            "environment",
            "timezone",
            "schedules",
            "notifications",
            "project",
            "workspace",
            "created_at",
            "modified_at",
        ]


class RequestJobRunSerializer(serializers.Serializer):
    payload = serializers.JSONField(required=False, allow_null=True)


class JobPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPayload
        fields = [
            "suuid",
            "size",
            "lines",
            "created_at",
            "modified_at",
        ]


class JobPayloadRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True, source="filename")
    size = serializers.IntegerField(read_only=True)
    lines = serializers.IntegerField(read_only=True)

    def get_relation(self, instance) -> str:
        return "payload"

    class Meta:
        model = JobPayload
        fields = [
            "relation",
            "suuid",
            "name",
            "size",
            "lines",
        ]


class RunImageRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    tag = serializers.CharField(read_only=True)
    digest = serializers.CharField(read_only=True)

    def get_relation(self, instance) -> str:
        return "image"

    class Meta:
        model = RunImage
        fields = [
            "relation",
            "suuid",
            "name",
            "tag",
            "digest",
        ]
