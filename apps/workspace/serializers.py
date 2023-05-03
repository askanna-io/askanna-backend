from rest_framework import serializers

from account.models.membership import Membership
from account.serializers.user import UserRelationSerializer
from core.permissions.askanna_roles import merge_role_permissions
from workspace.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = UserRelationSerializer(read_only=True)
    is_member = serializers.BooleanField(read_only=True)
    permission = serializers.SerializerMethodField()

    def get_permission(self, instance) -> dict[str, bool]:
        user_request_roles = self.context["request"].user_roles
        user_workspace_role = Membership.get_workspace_role(self.context["request"].user, instance)
        user_roles = user_request_roles + [user_workspace_role]
        return merge_role_permissions(user_roles)

    def create(self, validated_data):
        validated_data.update(**{"created_by": self.context["request"].user})
        instance = super().create(validated_data)
        instance.is_member = True
        return instance

    class Meta:
        model = Workspace
        fields = [
            "suuid",
            "name",
            "description",
            "visibility",
            "created_by",
            "is_member",
            "permission",
            "created_at",
            "modified_at",
        ]
        extra_kwargs = {
            "name": {
                "required": True,
                "allow_null": False,
                "allow_blank": False,
            },
        }


class WorkspaceRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    def get_relation(self, instance) -> str:
        return self.Meta.model.__name__.lower()

    class Meta:
        model = Workspace
        fields = [
            "relation",
            "suuid",
            "name",
        ]
