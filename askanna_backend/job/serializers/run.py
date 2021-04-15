# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
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
    runner = serializers.SerializerMethodField("get_runner")

    payload = serializers.SerializerMethodField("get_payload")

    jobdef = serializers.SerializerMethodField("get_jobdef")

    metricsmeta = serializers.SerializerMethodField("get_metricsmeta")
    variablesmeta = serializers.SerializerMethodField("get_variablesmeta")

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
        ]
