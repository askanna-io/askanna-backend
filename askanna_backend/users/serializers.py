from rest_framework import serializers
from users.models import Membership, UserProfile, Invitation, ROLES, MEMBERSHIPS
from django.utils import timezone
from datetime import timedelta
from django.core import signing
from django.db.models import Q
from django.db.models import Model

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = "__all__"


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
    name = ReadWriteSerializerMethodField("get_name")
    status = ReadWriteSerializerMethodField("get_status", required=False)
    email = ReadWriteSerializerMethodField('get_email')
    uuid = serializers.UUIDField(read_only=True)
    short_uuid = serializers.CharField(read_only=True)
    object_uuid = serializers.UUIDField()
    object_type = serializers.ChoiceField(choices=MEMBERSHIPS, default= 'WS')
    role = serializers.ChoiceField(choices=ROLES, default='WM')
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    user = serializers.CharField(read_only=True)
    token = serializers.CharField(write_only=True)

    token_signer = signing.TimestampSigner()

    class Meta:
        fields = "__all__"

    def generate_token(self):
        """
        This function returns the token with as value the uuid of the instance
        """

        return self.token_signer.sign(self.instance.uuid)

    def get_name(self, instance):
        """
        This function gets the name from the user.
        Either from the invitation or from the already accepted memberships.
        """
        try:
            instance.invitation.name
        except Invitation.DoesNotExist:
            return instance.user.get_name()
        return instance.invitation.name

    def get_email(self, instance):
        """
        This function checks if there already exist an invitation.
        If it does then it uses the email from the invitation, otherwise it uses the email of the user.
        """
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            return instance.user.email
        else:
            return instance.invitation.email

    def get_status(self, instance):
        """
        This function returns the status 'accepted' if the invitation doesn't exist.
            Since the invitation has be removed if it is accepted
        """
        if not isinstance(instance, Model):
            return None
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            return "accepted"
        else:
            return "invited"

    def validate_status(self, value):
        """
        The function validates the status value. It only accepts the value: accepted
        """

        if value != {'status': 'accepted'}:
            raise serializers.ValidationError("Status is not accepted")

        return value

    def validate_token(self, value):
        """
        This function validates the token and raises a validation error in the following cases:
            1. If the max_age of the token passed
            2. If the token passed doesn't match the actual token
        """
        try:
            unsigned_value = self.token_signer.unsign(value, max_age=timedelta(days=7))
        except signing.SignatureExpired:
            raise serializers.ValidationError("Token expired")
        except signing.BadSignature:
            raise serializers.ValidationError("Token is not valid")

        if str(self.instance.uuid) != unsigned_value:
            raise serializers.ValidationError("Token does not match for this workspace")

        return unsigned_value

    def change_membership_to_accepted(self, instance):
        """
        The function deletes the invitation, but keeps the membership that is connected to this.
                It creates a userprofile for the membership
                    This can only be done by authenticated users
        """
        instance.invitation.delete(keep_parents=True)
        userprofile = UserProfile()
        userprofile.membership_ptr = instance
        userprofile.save_base(raw=True)
        instance.user = self._context['request'].user


    def create(self, validated_data):
        """
        This function creates the Invitation
        """
        return Invitation.objects.create(**validated_data)

    def validate(self, data):
        """
        The token is needed to be able to accept the invitation.
        This function validates the data by checking if there exists a token and the status is accepted.
        """
        data = super().validate(data)

        self.validate_token_for_workspace(data)
        self.validate_email_is_unique(data)
        self.validate_user_in_membership(data)

        return data

    def validate_token_for_workspace(self, data):

         if "status" in data:
            if data['status']=='accepted' and self.get_status(self.instance) == 'invited':
                if "token" not in data:
                    raise serializers.ValidationError("Token is required when accepting invitation")

    def validate_email_is_unique(self, data):
        """
        This function validates whether the email is unique for the membership.
        If the email already exist it raises a ValidationError.
        """
        if 'email' in data:
            email = data['email']
            membership = data['object_uuid']

            if Membership.objects.filter(Q(invitation__email=email) | Q(user__email=email)).filter(object_uuid=membership).exists():
                raise serializers.ValidationError("This email already belongs to this membership")


    def validate_user_in_membership(self, data):
        """
        This function validates whether the user is unique for the membership.
        If the user is already part of the membership it raises an ValidationError.
        """
        if "status" in data:
            if data['status'] == 'accepted' and self.get_status(self.instance) == 'invited':
                user = self._context['request'].user
                if Membership.objects.filter(Q(user=user)).exists():
                    raise serializers.ValidationError("User is already part of this workspace")


    def update(self, instance, validated_data):
        """
        This function does the following:
            1. if the request changes the status to accepted when the initial status is invited and there exists a token,
                the change_membership_to_accepted function is called
            2. It updates the fields that are given in the validated_data and reloads model values from the database
        """
        status = validated_data.get('status', None)
        if status == 'accepted'and self.get_status(instance) == 'invited' and self.generate_token():
            self.change_membership_to_accepted(instance)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        instance.refresh_from_db()

        return instance

    def get_fields(self):
        """
        This function should delete the token if the status is accepted or if the invitation doesn't exist anymore
        """
        fields = super().get_fields()
        if not self.instance or self.get_status(self.instance) == 'accepted':
            del fields['token']

        if self.instance:
            fields['email'].read_only = True
            fields['object_uuid'].read_only = True
            fields['object_type'].read_only = True

        return fields
