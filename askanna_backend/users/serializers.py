from rest_framework import serializers
from users.models import Membership


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField("get_user")
    role = serializers.SerializerMethodField("get_role")

    def get_role(self, obj):
        if obj.role == "1":
            return "Member"
        else:
            return obj.get_role_display()

    def get_user(self, instance):
        user = instance.user
        return {
            "uuid": user.uuid,
            "short_uuid": user.short_uuid,
            "name": user.get_name(),
            "created": user.created,
            "last_active": "",

        }

    class Meta:
        model = Membership
        fields = ['user', 'role']

    def to_representation(self, instance):
        request = self.context["request"]
        role = self.fields['role']
        role_value = role.to_representation(
            role.get_attribute(instance))
        url = "{scheme}://{host}/workspace/{short_uuid}/people".format(
            scheme=request.scheme,
            host=request.get_host().replace("-api", "").replace("api", ""),
            short_uuid= instance.short_uuid,
        )
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.user.get_name(),
            "role": role_value,
            "created": instance.created,
            "last_active": "",
        }


class UpdateUserRoleSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField("get_role")

    class Meta:
        model = Membership
        fields = ["role"]

    def get_role(self, obj):
        return obj.get_role_display()

    def update(self, instance, validated_data):
        instance.role = validated_data.get("role", instance.role)
        instance.save()
        return instance

    def validated_role(self, role):
        """
        Validation of a given new value for value
        """
        return role

    def to_representation(self, instance):
        role = self.fields['role']
        role_value = role.to_representation(
            role.get_attribute(instance))
        return {
            'uuid': instance.uuid,
            'short_uuid': instance.short_uuid,
            "name": instance.user.get_name(),
            "role": role_value,
            "created": instance.created,
            "last_active": "",
            "message": "Successfully changed the role",
        }

# class MembershipCreateSerializer(serializers.ModelSerializer):
#     user = serializers.SerializerMethodField("create_user")
#
#     class Meta:
#         model = Membership
#         fields = ["user", "object_type", "object_uuid"]
#
#     def create_user(self, validated_data):
#         validated_data.update(**{"user": self.context["request"].user})
#         return super().create(validated_data)
#
#     #TODO: validation of existing user
#     def to_representation(self, instance):
#         request = self.context["request"]
#         url = "{scheme}://{host}/workspace/{short_uuid}/people".format(
#             scheme=request.scheme,
#             host=request.get_host().replace("-api", "").replace("api", ""),
#             short_uuid= instance.short_uuid,
#         )
#         return {
#             "uuid": instance.uuid,
#             "short_uuid": instance.short_uuid,
#             "name": instance.user.get_name(),
#             "role": instance.get_role(),
#             "created": instance.created,
#             "last_active": "",
#             "message": "Successfully added new member",
#         }
