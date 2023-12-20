from rest_framework import serializers

from account.models.membership import Membership
from account.serializers.user import RoleSerializer
from storage.serializers import FileDownloadInfoSerializer


class MembershipRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True, source="get_name")
    job_title = serializers.CharField(read_only=True, source="get_job_title")
    role = RoleSerializer(read_only=True, source="get_role")
    avatar_file = FileDownloadInfoSerializer(read_only=True, source="get_avatar_file")
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
            "avatar_file",
            "status",
        )
