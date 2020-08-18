from rest_framework import serializers
from users.models import Membership


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField("get_user")

    def get_user(self, instance):
        user = instance.user
        return {
            "uuid": user.uuid,
            "short_uuid": user.short_uuid,
            "name": user.get_name(),
            "role": "member",
            "created": user.created,
            "last_active": "",

        }

    class Meta:
        model = Membership
        fields = ['user']

    def to_representation(self, instance):
        request = self.context["request"]
        url = "{scheme}://{host}/workspace/{short_uuid}/people".format(
            scheme=request.scheme,
            host=request.get_host().replace("-api", "").replace("api", ""),
            short_uuid= instance.short_uuid,
        )
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.user.get_name(),
            "role": "member",
            "created": instance.created,
            "last_active": "",
        }

