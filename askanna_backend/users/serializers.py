from rest_framework import serializers
from users.models import Membership, UserProfile, Invitation, ROLES, MEMBERSHIPS
from django.utils import timezone
from datetime import timedelta
from django.core.signing import TimestampSigner


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
        instance.refresh_from_db()
        return instance

    def validated_role(self, role):
        """
        Validation of a given new value for role
        """
        return role

    def to_representation(self, instance):
        request = self.context["request"]
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.user.get_name(),
            "job_title": instance.job_title,
            "role": instance.role,
            "created": instance.created,
            "last_active": "",
            "message": "Successfully changed the role"
   }


class ReadWriteSerializerMethodField(serializers.Field):
   def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source']= '*'
        kwargs['read_only'] = False
        super().__init__(**kwargs)

   def bind(self, field_name, parent):
        # The method name defaults to `get_{field_name}`.
        if self.method_name is None:
            self.method_name = 'get_{field_name}'.format(field_name=field_name)

        super().bind(field_name, parent)

   def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)

   def to_internal_value(self, data):
        return {self.field_name: data}

class PersonSerializer(serializers.Serializer):
    status = ReadWriteSerializerMethodField("get_status", required=False)
    email = ReadWriteSerializerMethodField('get_email')
    expiry_date = serializers.DateTimeField(source='invitation.expiry_date', read_only=True)
    object_uuid = serializers.UUIDField()
    object_type = serializers.ChoiceField(choices=MEMBERSHIPS, default= 'WS')
    role = serializers.ChoiceField(choices=ROLES, default='WM')
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    user = serializers.CharField(read_only=True)
    token = serializers.SerializerMethodField('generate_token', read_only=True)

    class Meta:
        fields = "__all__"

    def generate_token(self, instance):
        token = TimestampSigner()
        instance.token = token.sign('invitation token')
        return instance.token

    def get_email(self, instance):
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            return instance.user.email
        else:
            return instance.invitation.email

    def get_status(self, instance):
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            return "accepted"
        else:
            return "invited"

    def validate_token(self, instance):
        if instance.invitation and instance.invitation.token.unsign(token, max_age=expiry_date):
            return True
        else:
            raise serializers.ValidationError("Invitation is not valid")
            return False

    def change_membership_to_accepted(self, instance):
        instance.invitation.delete(keep_parents=True)
        userprofile = UserProfile()
        userprofile.membership_ptr = instance
        userprofile.save_base(raw=True)
        instance.user = self._context['request'].user

    def create(self, validated_data):
        expiry_date = timezone.now() + timedelta(days=7)
        return Invitation.objects.create(expiry_date=expiry_date, **validated_data)

    def update(self, instance, validated_data):
        print(validated_data)
        status = validated_data.get('status', None)
        if status == 'accepted'and self.get_status(instance) == 'invited' and self.generate_token(instance):
            self.change_membership_to_accepted(instance)


        instance.object_uuid = validated_data.get('object_uuid', instance.object_uuid)
        instance.object_type = validated_data.get('object_type', instance.object_type)
        instance.role = validated_data.get('role', instance.role)
        instance.job_title = validated_data.get('job_title', instance.job_title)
        instance.save()
        instance.refresh_from_db()
        return instance

    def get_fields(self):
        fields = super().get_fields()
        if self.instance and self.get_status(self.instance) == 'accepted':
            del fields['expiry_date']
        return fields
