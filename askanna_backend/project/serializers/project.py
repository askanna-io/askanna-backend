from typing import Dict

from project.models import Project
from rest_framework import serializers
from users.models import MSP_WORKSPACE, Membership
from workspace.models import Workspace


class BaseProjectSerializer:
    created_by = serializers.SerializerMethodField("get_created_by")
    is_member = serializers.SerializerMethodField("get_is_member")
    permission = serializers.SerializerMethodField("get_permission")
    workspace = serializers.SerializerMethodField("get_workspace")
    package = serializers.SerializerMethodField("get_package")

    def get_is_member(self, instance):
        return instance.is_member

    def _get_true_permissions(self, permissions: Dict) -> Dict:
        return dict(filter(lambda x: x[1] is True, permissions.items()))

    def get_permission(self, instance):
        permissions = []
        role = self.context["request"].role
        object_roles = Membership.get_roles_for_project(self.context["request"].user, instance)
        if not role and not object_roles:
            return []
        permissions = role.full_permissions(role)
        true_permissions = self._get_true_permissions(permissions)

        for role in object_roles:
            # filter out `false` permissions, we don't want to override permissions already given as True
            role_permissions = role.full_permissions(role)
            role_true_permissions = self._get_true_permissions(role_permissions)
            true_permissions.update(**role_true_permissions)
            permissions.update(**role_permissions)
            permissions.update(**true_permissions)

        return permissions

    def get_workspace(self, instance):
        return instance.workspace.relation_to_json

    def get_created_by(self, instance):
        if instance.created_by:
            return instance.created_by.relation_to_json
        else:
            return None

    def get_package(self, instance):
        """
        Get references to the last pushed package for this project
        """
        package = instance.packages.order_by("-created").first()
        if package:
            return package.relation_to_json
        else:
            return None

    def to_representation(self, instance):
        request = self.context["request"]
        url = "{scheme}://{host}/{workspace}/project/{project}".format(
            scheme=request.scheme,
            host=request.get_host().replace("-api", "").replace("api.", ""),
            workspace=instance.workspace.suuid,
            project=instance.suuid,
        )
        return {
            "suuid": instance.suuid,
            "name": instance.get_name(),
            "description": instance.description,
            "workspace": self.get_workspace(instance),
            "package": self.get_package(instance),
            "permission": self.get_permission(instance),  # this is relative to the user requesting this
            "is_member": self.get_is_member(instance),
            "created_by": self.get_created_by(instance),
            "visibility": instance.visibility,
            "created": instance.created,
            "modified": instance.modified,
            "url": url,
        }


class ProjectSerializer(BaseProjectSerializer, serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = [
            "uuid",
            "deleted",
            "activate_date",
            "deactivate_date",
            "status",
        ]


class ProjectUpdateSerializer(BaseProjectSerializer, serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "description", "visibility"]

    def validate_visibility(self, value):
        if not value.upper() in ["PRIVATE", "PUBLIC"]:
            raise serializers.ValidationError(f"`visibility` can only be PUBLIC or PRIVATE, not {value}")
        return value.upper()

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.visibility = validated_data.get("visibility", instance.visibility)
        instance.save()
        instance.refresh_from_db()
        return instance


class ProjectCreateSerializer(BaseProjectSerializer, serializers.ModelSerializer):
    workspace = serializers.CharField(max_length=19)

    def get_is_member(self, instance):
        # always true since we where able to create the project
        return True

    class Meta:
        model = Project
        fields = ["name", "workspace", "description", "visibility"]

    def create(self, validated_data):
        validated_data.update(**{"created_by": self.context["request"].user})
        return super().create(validated_data)

    def validate_workspace(self, value):
        """
        Validation of a given workspace suuid

        Steps needed:
        - check in database for existing workspace with suuid
        - check whether the user is a member of this workspace
        - return the workspace.uuid instead of suuid in `value`

        In all cases of error, return a message that workspace doesn't exist or user has no access

        """
        try:
            workspace = Workspace.objects.get(suuid=value)
        except Exception:
            raise serializers.ValidationError("Workspace with SUUID={} was not found".format(value))
        else:
            # check whether the user has access to this workspace

            is_member = (
                self.context["request"]
                .user.memberships.filter(object_type=MSP_WORKSPACE, object_uuid=workspace.uuid)
                .count()
                > 0
            )
            if is_member:
                return workspace
            else:
                raise serializers.ValidationError("User is not member of workspace {}".format(value))

        return value

    def validate_visibility(self, value):
        if not value.upper() in ["PRIVATE", "PUBLIC"]:
            raise serializers.ValidationError(f"`visibility` can only be PUBLIC or PRIVATE, not {value}")
        return value.upper()
