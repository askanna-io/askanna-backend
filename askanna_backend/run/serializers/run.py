from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers
from run.models import Run


class RunSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField("get_job")
    project = serializers.SerializerMethodField("get_project")
    workspace = serializers.SerializerMethodField("get_workspace")

    created_by = serializers.SerializerMethodField("get_created_by")

    environment = serializers.SerializerMethodField("get_environment")
    package = serializers.SerializerMethodField("get_package")
    payload = serializers.SerializerMethodField("get_payload")

    result = serializers.SerializerMethodField("get_result")
    artifact = serializers.SerializerMethodField("get_artifact")
    metrics_meta = serializers.SerializerMethodField("get_metrics_meta")
    variables_meta = serializers.SerializerMethodField("get_variables_meta")
    log = serializers.SerializerMethodField("get_log")

    duration = serializers.SerializerMethodField("get_duration")

    def get_metrics_meta(self, instance):
        try:
            metrics = instance.metrics.get()
        except ObjectDoesNotExist:
            return {
                "count": 0,
                "size": 0,
                "metric_names": [],
                "label_names": [],
            }
        return {
            "count": metrics.count,
            "size": metrics.size,
            "metric_names": metrics.metric_names or [],
            "label_names": metrics.label_names or [],
        }

    def get_variables_meta(self, instance):
        try:
            runvariables = instance.runvariables.get()
        except ObjectDoesNotExist:
            return {
                "count": 0,
                "size": 0,
                "variable_names": [],
                "label_names": [],
            }

        # For the frontend we make sure that if labels 'source' and/or 'is_masked' are in the label_names dictionary,
        # that we add them as the first label in the list.
        label_names = []
        if runvariables.label_names:
            label_names = list(filter(lambda x: x["name"] != "is_masked", runvariables.label_names))
            if len(label_names) != len(runvariables.label_names):
                label_names = [{"name": "is_masked", "type": "tag"}] + label_names
            label_names = list(filter(lambda x: x["name"] != "source", label_names))
            if len(label_names) != len(runvariables.label_names):
                label_names = [{"name": "source", "type": "string"}] + label_names

        return {
            "count": runvariables.count,
            "size": runvariables.size,
            "variable_names": runvariables.variable_names or [],
            "label_names": label_names,
        }

    def get_duration(self, instance):
        if instance.duration or instance.duration == 0:
            return instance.duration

        # Calculate the duration or return 0
        if not instance.started:
            return 0
        if instance.finished:
            return (instance.finished - instance.started).seconds
        return (timezone.now() - instance.started).seconds

    def get_environment(self, instance):
        environment = {
            "name": instance.environment_name,
            "image": None,
            "timezone": instance.timezone,
        }
        if instance.run_image:
            environment["image"] = instance.run_image.relation_to_json
        return environment

    def get_payload(self, instance):
        try:
            return instance.payload.relation_to_json
        except AttributeError or ObjectDoesNotExist:
            return None

    def get_result(self, instance):
        try:
            return instance.result.relation_to_json
        except AttributeError or ObjectDoesNotExist:
            return None

    def get_job(self, instance):
        return instance.jobdef.relation_to_json

    def get_artifact(self, instance):
        try:
            artifact = instance.artifact.first()
            return artifact.relation_to_json
        except AttributeError or ObjectDoesNotExist:
            return None

    def get_package(self, instance):
        if instance.package:
            return instance.package.relation_to_json
        return None

    def get_workspace(self, instance):
        workspace = instance.jobdef.project.workspace
        return workspace.relation_to_json

    def get_project(self, instance):
        project = instance.jobdef.project
        return project.relation_to_json

    def get_created_by(self, instance):
        if instance.member:
            return instance.member.relation_to_json_with_avatar
        if instance.created_by:
            return instance.created_by.relation_to_json
        return None

    def get_log(self, instance):
        try:
            return instance.output.relation_to_json
        except ObjectDoesNotExist:
            return None

    class Meta:
        model = Run
        fields = [
            "suuid",
            "name",
            "description",
            "status",
            "started",
            "finished",
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
            "created",
            "modified",
        ]


class RunUpdateSerializer(RunSerializer):
    def update(self, instance, validated_data):
        """ "
        Allow updates on `name` and `description` only. Ignore other fields
        """
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save(update_fields=["name", "description", "modified"])
        instance.refresh_from_db()
        return instance
