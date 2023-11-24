from rest_framework import serializers

from account.serializers.membership import MembershipWithAvatarRelationSerializer
from core.permissions.role_utils import get_user_workspace_role, merge_role_permissions
from workspace.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = MembershipWithAvatarRelationSerializer(read_only=True, source="created_by_member")
    is_member = serializers.BooleanField(read_only=True)
    permission = serializers.SerializerMethodField()

    def get_permission(self, instance) -> dict[str, bool]:
        user_request_roles = self.context["request"].user_roles
        user_workspace_role = get_user_workspace_role(self.context["request"].user, instance)
        user_roles = user_request_roles + [user_workspace_role]
        return merge_role_permissions(user_roles)

    def create(self, validated_data):
        validated_data.update(**{"created_by_user": self.context["request"].user})
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
