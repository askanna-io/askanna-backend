from typing import Dict

from rest_framework import serializers
from users.models import Membership
from workspace.models import Workspace


class BaseWorkspaceSerializer(serializers.ModelSerializer):
    is_member = serializers.SerializerMethodField("get_is_member")
    permission = serializers.SerializerMethodField("get_permission")
    created_by = serializers.SerializerMethodField("get_created_by")

    def get_created_by(self, instance):
        if instance.created_by:
            return instance.created_by.relation_to_json
        else:
            return None

    def to_representation(self, instance):
        request = self.context["request"]
        url = "{scheme}://{host}/{workspace}/".format(
            scheme=request.scheme,
            host=request.get_host().replace("-api", "").replace("api.", ""),
            workspace=instance.suuid,
        )
        return {
            "suuid": instance.suuid,
            "name": instance.get_name(),
            "description": instance.description,
            "visibility": instance.visibility,
            "created_by": self.get_created_by(instance),
            "permission": self.get_permission(instance),  # this is relative to the user requesting this
            "is_member": self.get_is_member(instance),
            "created": instance.created,
            "modified": instance.modified,
            "url": url,
        }

    @staticmethod
    def get_is_member(instance):
        return instance.is_member

    def get_permission(self, instance):
        permissions = []
        role = self.context["request"].role
        workspace_role, _ = Membership.get_workspace_role(self.context["request"].user, instance)

        if not role and not workspace_role:
            return []

        permissions = role.full_permissions(role)
        true_permissions = self._get_true_permissions(permissions)

        workspace_role_permissions = workspace_role.full_permissions(workspace_role)
        true_permissions.update(**workspace_role_permissions)
        permissions.update(**workspace_role_permissions)
        permissions.update(**true_permissions)

        return permissions

    @staticmethod
    def _get_true_permissions(permissions: Dict) -> Dict:
        return dict(filter(lambda x: x[1] is True, permissions.items()))

    @staticmethod
    def validate_visibility(value):
        if value.upper() not in ["PRIVATE", "PUBLIC"]:
            raise serializers.ValidationError(f"`visibility` can only be PUBLIC or PRIVATE, not {value}")
        return value.upper()


class WorkspaceSerializer(BaseWorkspaceSerializer):
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.visibility = validated_data.get("visibility", instance.visibility)
        instance.save()
        instance.refresh_from_db()
        return instance

    class Meta:
        model = Workspace
        exclude = [
            "deleted",
            "activate_date",
            "deactivate_date",
            "status",
        ]


class WorkspaceCreateSerializer(BaseWorkspaceSerializer):
    def create(self, validated_data):
        validated_data.update(**{"created_by": self.context["request"].user})
        return super().create(validated_data)

    class Meta:
        model = Workspace
        fields = (
            "name",
            "description",
            "visibility",
        )
        extra_kwargs = {
            "name": {
                "required": True,
                "allow_null": False,
                "allow_blank": False,
            }
        }

    def get_is_member(self, instance):
        # Always true since it was possible to create the workspace
        return True
