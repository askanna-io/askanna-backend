from core.utils import get_setting_from_database
from django.conf import settings
from job.models import JobDef, JobPayload
from package.models import Package
from rest_framework import serializers


class JobSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField("get_project")
    environment = serializers.SerializerMethodField("get_environment")
    schedules = serializers.SerializerMethodField("get_schedules")

    notifications = serializers.SerializerMethodField("get_notifications")

    def get_notifications(self, instance):
        """
        If notifications are configured we return them here
        """
        package = Package.objects.filter(project=instance.project).order_by("-created").first()

        configyml = package.get_askanna_config()
        if configyml is None:
            # we could not parse the config
            return {}

        job = configyml.jobs.get(instance.name)
        if job and job.notifications:
            return job.notifications

        return {}

    def get_default_image(self, instance):
        return get_setting_from_database(
            name="RUNNER_DEFAULT_DOCKER_IMAGE",
            default=settings.RUNNER_DEFAULT_DOCKER_IMAGE,
        )

    def get_project(self, instance):
        return instance.project.relation_to_json

    def get_environment(self, instance):
        return instance.environment_image or self.get_default_image(instance)

    def get_schedules(self, instance):
        schedules = instance.schedules.order_by("next_run")
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

    class Meta:
        model = JobDef
        exclude = ("deleted", "environment_image")


class StartJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = "__all__"


class JobPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPayload
        exclude = ("jobdef", "owner")
