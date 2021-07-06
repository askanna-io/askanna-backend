# -*- coding: utf-8 -*-
import os

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from job.models import JobRun, JobPayload


class JobPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPayload
        exclude = ("jobdef", "owner")


class JobRunSerializer(serializers.ModelSerializer):
    artifact = serializers.SerializerMethodField("get_artifact")
    package = serializers.SerializerMethodField("get_package")
    project = serializers.SerializerMethodField("get_project")
    owner = serializers.SerializerMethodField("get_user")

    payload = serializers.SerializerMethodField("get_payload")
    result = serializers.SerializerMethodField("get_result")

    jobdef = serializers.SerializerMethodField("get_jobdef")

    metricsmeta = serializers.SerializerMethodField("get_metricsmeta")
    variablesmeta = serializers.SerializerMethodField("get_variablesmeta")

    duration = serializers.SerializerMethodField("get_duration")
    environment = serializers.SerializerMethodField("get_environment")

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

    def get_variablesmeta(self, instance):
        try:
            runvariables = instance.runvariables.get()
        except ObjectDoesNotExist:
            return {
                "count": 0,
                "size": 0,
                "labels": [
                    "source",
                ],
                "keys": [],
            }
        special_labels = ["source"]
        if "is_masked" in instance.variable_labels:
            special_labels.append("is_masked")
        return {
            "count": runvariables.count,
            "size": runvariables.size,
            "labels": special_labels
            + list(set(instance.variable_labels) - set(special_labels)),
            "keys": instance.variable_keys,
        }

    def get_duration(self, instance):
        if not instance.duration or not instance.is_finished:
            # calculate the duration because we are still running
            if not instance.started:
                return 0
            return (timezone.now() - instance.started).seconds
        return instance.duration

    def get_environment(self, instance):
        environment = {
            "name": instance.environment_name,
            "description": None,
            "label": None,
            "image": None,
            "timezone": instance.timezone,
        }
        if instance.run_image:
            environment["image"] = {
                "name": instance.run_image.name,
                "tag": instance.run_image.tag,
                "digest": instance.run_image.digest,
            }
        return environment

    def get_payload(self, instance):
        payload = JobPayloadSerializer(instance.payload, many=False)
        return payload.data

    def get_result(self, instance):
        try:
            result = instance.result
        except ObjectDoesNotExist:
            return None

        extension = None
        if result.name:
            filename, extension = os.path.splitext(result.name)
            if extension == "":
                extension = filename
            if extension.startswith("."):
                extension = extension[1:]

        return {
            "size": result.size,
            "lines": result.lines,
            "original_name": result.name,
            "extension": extension,
            "mimetype": result.mime_type,
        }

    def get_jobdef(self, instance):
        jobdef = instance.jobdef
        return jobdef.relation_to_json

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
            "variable_keys",
            "variable_labels",
            "deleted",
            "environment_name",
            "timezone",
            "run_image",
        ]


class JobRunUpdateSerializer(JobRunSerializer):
    def update(self, instance, validated_data):
        """ "
        Allow updates on `name` and `description` only. Ignore other fields
        """
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save(update_fields=["name", "description", "modified"])
        instance.refresh_from_db()
        return instance
