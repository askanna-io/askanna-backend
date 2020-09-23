from rest_framework import serializers
from users.models import Membership, UserProfile, Invitation, ROLES, MEMBERSHIPS


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

# STATUS = (
#     ("invited", "invited"),
#     ("accepted", "accepted"),
# )
class PersonSerializer(serializers.Serializer):
    status = serializers.SerializerMethodField("get_status")

    email = serializers.EmailField(max_length=None, allow_blank=False)
    expiry_date = serializers.DateTimeField()
    object_uuid = serializers.UUIDField()
    object_type = serializers.ChoiceField(choices=MEMBERSHIPS, default='WS')
    role = serializers.ChoiceField(choices=ROLES, default='WM')
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    user = serializers.CharField(required=False, allow_blank=True, max_length=255)

    class Meta:
        fields = "__all__"

    def get_status(self, instance):
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            pass
        else:
            return "invited"

    def create(self, validated_data):
        return Invitation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.email = validated_data.get('email', instance.email)
        instance.expiry_date = validated_data.get('expiry_date', instance.expiry_date)
        instance.object_uuid = validated_data.get('object_uuid', instance.object_uuid)
        instance.object_type = validated_data.get('object_type', instance.object_type)
        instance.role = validated_data.get('role', instance.role)
        instance.job_title = validated_data.get('job_title', instance.job_title)
        instance.user = validated_data.get('user', instance.user)
        instance.save()
        return instance


