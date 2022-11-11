from core.utils import get_setting_from_database
from django.conf import settings
from job.models import JobDef, JobPayload
from rest_framework import serializers


class JobSerializer(serializers.ModelSerializer):
    workspace = serializers.SerializerMethodField("get_workspace")
    project = serializers.SerializerMethodField("get_project")
    environment = serializers.SerializerMethodField("get_environment")
    schedules = serializers.SerializerMethodField("get_schedules")

    notifications = serializers.SerializerMethodField("get_notifications")

    def get_notifications(self, instance):
        """
        If notifications are configured we return them here
        """
        package = instance.project.packages.order_by("-created").first()

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

    def get_default_image(self, instance):
        return get_setting_from_database(
            name="RUNNER_DEFAULT_DOCKER_IMAGE",
            default=settings.RUNNER_DEFAULT_DOCKER_IMAGE,
        )

    def get_workspace(self, instance):
        return instance.project.workspace.relation_to_json

    def get_project(self, instance):
        return instance.project.relation_to_json

    def get_environment(self, instance):
        return instance.environment_image or self.get_default_image(instance)

    def get_schedules(self, instance):
        schedules = instance.schedules.order_by("next_run")
        if schedules:
            return [
                {
                    "raw_definition": schedule.raw_definition,
                    "cron_definition": schedule.cron_definition,
                    "cron_timezone": schedule.cron_timezone,
                    "next_run": schedule.next_run,
                    "last_run": schedule.last_run,
                }
                for schedule in schedules
            ]
        return None

    class Meta:
        model = JobDef
        fields = [
            "suuid",
            "name",
            "description",
            "workspace",
            "project",
            "environment",
            "timezone",
            "schedules",
            "notifications",
            "created",
            "modified",
        ]


class StartJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = "__all__"


class JobPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPayload
        fields = [
            "suuid",
            "size",
            "lines",
            "created",
            "modified",
        ]
