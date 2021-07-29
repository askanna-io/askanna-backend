# -*- coding: utf-8 -*-
from rest_framework import serializers

from package.models import Package
from project.models import Project
from users.models import MSP_WORKSPACE
from workspace.models import Workspace


class BaseProjectSerializer:
    def get_workspace(self, instance):
        return instance.workspace.relation_to_json

    def get_created_by(self, instance):
        if instance.created_by is not None:
            return {
                "uuid": instance.created_by.uuid,
                "short_uuid": instance.created_by.short_uuid,
                "name": instance.created_by.get_name(),
            }
        return {
            "uuid": None,
            "short_uuid": None,
            "name": None,
        }

    def get_package(self, instance):
        """
        Get references to the last pushed package for this project
        """
        package = instance.packages.order_by("-created").first()

        if package:
            return {
                "uuid": package.uuid,
                "short_uuid": package.short_uuid,
                "name": package.original_filename,
            }
        return {
            "uuid": None,
            "short_uuid": None,
            "name": None,
        }

    notifications = serializers.SerializerMethodField("get_notifications")

    def get_notifications(self, instance):
        """
        If notifications are configured we return them here
        """
        package = Package.objects.filter(project=instance).order_by("-created").first()
        if not package:
            return {}

        configyml = package.get_askanna_config()
        if configyml is None:
            # we could not parse the config
            return {}

        if configyml.notifications:
            return configyml.notifications

        return {}

    def to_representation(self, instance):
        request = self.context["request"]
        url = "{scheme}://{host}/{workspace}/project/{project}".format(
            scheme=request.scheme,
            host=request.get_host().replace("-api", "").replace("api.", ""),
            workspace=instance.workspace.short_uuid,
            project=instance.short_uuid,
        )
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.get_name(),
            "description": instance.description,
            "workspace": self.get_workspace(instance),
            "package": self.get_package(instance),
            "notifications": self.get_notifications(instance),
            "template": instance.template,
            "created_by": self.get_created_by(instance),
            "created": instance.created,
            "modified": instance.modified,
            "url": url,
        }


class ProjectSerializer(BaseProjectSerializer, serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField("get_created_by")
    workspace = serializers.SerializerMethodField("get_workspace")
    package = serializers.SerializerMethodField("get_package")

    class Meta:
        model = Project
        exclude = [
            "deleted",
            "activate_date",
            "deactivate_date",
        ]


class ProjectUpdateSerializer(BaseProjectSerializer, serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "description"]

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance


class ProjectCreateSerializer(BaseProjectSerializer, serializers.ModelSerializer):
    workspace = serializers.CharField(max_length=19)

    class Meta:
        model = Project
        fields = ["name", "workspace", "description"]

    def create(self, validated_data):
        validated_data.update(**{"created_by": self.context["request"].user})
        return super().create(validated_data)

    def validate_workspace(self, value):
        """
        Validation of a given workspace short_uuid

        Steps needed:
        - check in database for existing workspace with short_uuid
        - check whether the user is a member of this workspace
        - return the workspace.uuid instead of short_uuid in `value`

        In all cases of error, return a message that workspace doesn't exist or user has no access

        """
        try:
            workspace = Workspace.objects.get(short_uuid=value)
        except Exception as e:
            print(e)
            raise serializers.ValidationError(
                "Workspace with SUUID={} was not found".format(value)
            )
        else:
            # check whether the user has access to this workspace

            is_member = (
                self.context["request"]
                .user.memberships.filter(
                    object_type=MSP_WORKSPACE, object_uuid=workspace.uuid
                )
                .count()
                > 0
            )
            if is_member:
                return workspace
            else:
                raise serializers.ValidationError(
                    "User is not member of workspace {}".format(value)
                )

        return value
