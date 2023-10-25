from rest_framework import serializers

from account.models.membership import Membership
from account.serializers.user import RoleSerializer


class MembershipRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source="get_name")
    job_title = serializers.ReadOnlyField(source="get_job_title")
    role = RoleSerializer(source="get_role")
    status = serializers.ReadOnlyField(source="get_status")

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
    avatar = serializers.DictField(source="get_avatar", read_only=True)

    class Meta(MembershipRelationSerializer.Meta):
        fields = MembershipRelationSerializer.Meta.fields + ("avatar",)
