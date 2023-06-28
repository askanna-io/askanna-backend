from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from job.models import JobDef, JobPayload, RunImage
from project.serializers import ProjectRelationSerializer
from workspace.serializers import WorkspaceRelationSerializer


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
    environment = serializers.ReadOnlyField(source="get_environment_image")
    timezone = serializers.ReadOnlyField()
    schedules = serializers.SerializerMethodField("get_schedules", allow_null=True)
    notifications = serializers.SerializerMethodField("get_notifications", allow_null=True)
    project = ProjectRelationSerializer(read_only=True)
    workspace = WorkspaceRelationSerializer(read_only=True, source="project.workspace")

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


class JobRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    def get_relation(self, instance) -> str:
        return self.Meta.model.__name__.lower()

    class Meta:
        model = JobDef
        fields = [
            "relation",
            "suuid",
            "name",
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
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source="filename")
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
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    tag = serializers.ReadOnlyField()
    digest = serializers.ReadOnlyField()

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
