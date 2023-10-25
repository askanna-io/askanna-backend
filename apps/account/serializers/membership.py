from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from account.models.membership import Membership
from account.serializers.user import AvatarSerializer, RoleSerializer


class MembershipRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True, source="get_name")
    job_title = serializers.CharField(read_only=True, source="get_job_title")
    role = RoleSerializer(read_only=True, source="get_role")
    status = serializers.CharField(read_only=True, source="get_status")

    def get_relation(self, instance) -> str:
        return self.Meta.model.__name__.lower()

    class Meta:
        model = Membership
        fields = (
            "relation",
            "suuid",
            "name",
            "job_title",
            "role",
            "status",
        )


class MembershipWithAvatarRelationSerializer(MembershipRelationSerializer):
    avatar_files = serializers.SerializerMethodField()

    @extend_schema_field(AvatarSerializer)
    def get_avatar_files(self, instance):
        avatar_files = instance.get_avatar_files()

        if avatar_files:
            return AvatarSerializer(avatar_files, context=self.context).data

        return None

    class Meta(MembershipRelationSerializer.Meta):
        fields = MembershipRelationSerializer.Meta.fields + ("avatar_files",)
