from rest_framework import serializers
from users.models import Membership, UserProfile, Invitation


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

STATUS = (
    (1, "invited"),
    (2, "accepted"),
)
class PersonSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=STATUS)
    class Meta:
        model = Invitation
        fields = "__all__"
