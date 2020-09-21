from rest_framework import serializers
from users.models import Membership, UserProfile


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField("get_user")
    role = serializers.SerializerMethodField("get_role")

    def get_user(self, instance):
        user = instance.user
        return {
            "uuid": user.uuid,
            "short_uuid": user.short_uuid,
            "name": user.get_name(),
            "job_title": user.job_title,
            "created": user.created,
            "last_active": "",

        }
    def get_role(self, obj):
        return obj.get_role_display()

    class Meta:
        model = Membership
        fields = ['user', 'role']

    def to_representation(self, instance):
        request = self.context["request"]
        role = self.fields['role']
        role_value = role.to_representation(
            role.get_attribute(instance))
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.user.get_name(),
            "job_title": instance.job_title,
            "role": role_value,
            "created": instance.created,
            "last_active": "",
   }


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = "__all__"


class UpdateUserRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Membership
        fields = ["role"]

    def update(self, instance, validated_data):
        instance.role = validated_data.get("role", instance.role)
        instance.save()
        return instance

    def validated_role(self, role):
        """
        Validation of a given new value for role
        """
        return role


# class MembershipCreateSerializer(serializers.ModelSerializer):
#     user = serializers.SerializerMethodField("create_user")
#
#     class Meta:
#         model = Membership
#         fields = ["user","role", "object_type", "object_uuid"]
#
#     def create_user(self, validated_data):
#         user = Membership.objects.create(validated_data)
#         return user
#         validated_data.update(**{"user": self.context["request"].user})
#         return super().create(validated_data)

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



