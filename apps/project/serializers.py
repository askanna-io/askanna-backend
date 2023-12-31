from rest_framework import serializers

from account.models.membership import Membership
from account.serializers.membership import MembershipWithAvatarRelationSerializer
from core.permissions.askanna_roles import merge_role_permissions
from package.serializers.package_relation import PackageRelationSerializer
from project.models import Project
from workspace.models import Workspace
from workspace.serializers import WorkspaceRelationSerializer


class ProjectSerializer(serializers.ModelSerializer):
    workspace = WorkspaceRelationSerializer(read_only=True)
    package = PackageRelationSerializer(allow_null=True, read_only=True, source="last_created_package")
    created_by = MembershipWithAvatarRelationSerializer(read_only=True, source="created_by_member")
    is_member = serializers.BooleanField(read_only=True)
    permission = serializers.SerializerMethodField()

    def get_permission(self, instance) -> dict[str, bool]:
        user_request_roles = self.context["request"].user_roles
        user_project_roles = Membership.get_roles_for_project(self.context["request"].user, instance)
        user_roles = user_request_roles + user_project_roles
        return merge_role_permissions(user_roles)

    class Meta:
        model = Project
        fields = [
            "suuid",
            "name",
            "description",
            "visibility",
            "workspace",
            "package",
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


class ProjectCreateSerializer(ProjectSerializer):
    workspace_suuid = serializers.SlugRelatedField(
        slug_field="suuid",
        write_only=True,
        required=True,
        queryset=Workspace.objects.active(),
        source="workspace",
    )

    def create(self, validated_data):
        validated_data.update(**{"created_by_user": self.context["request"].user})
        instance = super().create(validated_data)
        instance.is_member = True
        return instance

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["workspace_suuid"]


class ProjectRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    def get_relation(self, instance) -> str:
        return self.Meta.model.__name__.lower()

    class Meta:
        model = Project
        fields = [
            "relation",
            "suuid",
            "name",
        ]
