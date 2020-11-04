from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db.models import Q
from django.db.models import Model
from django.utils import timezone

from rest_framework import serializers

from users.models import Membership, User, UserProfile, Invitation, ROLES, MEMBERSHIPS
from workspace.models import Workspace


class ReadWriteSerializerMethodField(serializers.Field):
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs["source"] = "*"
        kwargs["read_only"] = False
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        if self.method_name is None:
            self.method_name = "get_{field_name}".format(field_name=field_name)
        super().bind(field_name, parent)

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)

    def to_internal_value(self, data):
        return {self.field_name: data}


class UserSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    email = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    short_uuid = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        """
        This function creates an user account and set the password
        """
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate(self, data):
        """
        This function validates the data
        """
        data = super().validate(data)
        self.validate_username(data)
        self.validate_email_is_unique(data)
        self.validate_password_length(data)
        self.validate_password_not_similar_username(data)

        return data

    def validate_username(self, data):
        """This function validates if the username is unique.
            If not, a ValidationError is raised"""
        if "username" in data:
            username = data["username"]

            if User.objects.filter(Q(username=username)).exists():
                raise serializers.ValidationError(
                    {"username": ["This username already exists"]}
                )

        return data

    def validate_email_is_unique(self, data):
        """This function validates if the email is unique"""
        if "email" in data:
            email = data["email"]

            if User.objects.filter(Q(email=email)).exists():
                raise serializers.ValidationError(
                    {"email": ["This email already exists"]}
                )

    def validate_password_length(self, data):
        """This function validates if the password is longer than 10 characters.
            If not, a ValidationError is raised"""

        if "password" in data:
            password = data["password"]

            if len(password) < 10:
                raise serializers.ValidationError(
                    {"password": ["The password should be longer than 10 characters"]}
                )

    def validate_password_not_similar_username(self, data):
        """This function validates if the password is not similar to the username.
            If this is the case, a ValidationError is raised """

        if "username" and "password" in data:
            if data["username"] in data["password"]:
                raise serializers.ValidationError(
                    {"password": ["The password should not be similar to the username"]}
                )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class PersonSerializer(serializers.Serializer):
    name = ReadWriteSerializerMethodField("get_name", required=False)
    status = ReadWriteSerializerMethodField("get_status", required=False)
    email = ReadWriteSerializerMethodField("get_email")
    uuid = serializers.UUIDField(read_only=True)
    short_uuid = serializers.CharField(read_only=True)
    object_uuid = serializers.UUIDField()
    # object_type = serializers.ChoiceField(choices=MEMBERSHIPS, default="WS")
    workspace = serializers.SerializerMethodField("get_workspace")
    role = serializers.ChoiceField(choices=ROLES, default="WM")
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    user = serializers.SerializerMethodField("get_user")
    token = serializers.CharField(write_only=True)
    front_end_url = serializers.CharField(
        required=False, default=settings.ASKANNA_UI_URL
    )

    token_signer = signing.TimestampSigner()

    class Meta:
        # fields = "__all__"
        exclude = ["object_uuid", "object_type"]

    def generate_token(self):
        """
        This function returns the token with as value the uuid of the instance
        """

        return self.token_signer.sign(self.instance.uuid)

    def get_workspace(self, instance):
        """
        object_type=WS
        object_uuid=uuid to Workspace
        """
        workspace = Workspace.objects.get(uuid=instance.object_uuid)
        return {
            "name": workspace.title,
            "short_uuid": workspace.short_uuid,
            "uuid": workspace.uuid,
        }

    def get_user(self, instance):
        if instance.user:
            return {
                "name": instance.user.get_name(),
                "short_uuid": instance.user.short_uuid,
                "uuid": instance.user.uuid,
            }
        return {
            "name": None,
            "short_uuid": None,
            "uuid": None,
        }

    def get_name(self, instance):
        """
        This function gets the name from the user.
        Either from the invitation or from the already accepted memberships.
        """
        try:
            instance.invitation.name
        except Invitation.DoesNotExist:
            if instance.user:
                return instance.user.get_name()
            return None
        else:
            return instance.invitation.name

    def get_email(self, instance):
        """
        This function checks if there already exist an invitation.
        If it does then it uses the email from the invitation, otherwise it uses the email of the user.
        """
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            if instance.user:
                return instance.user.email
            return None
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

        if value != {"status": "accepted"}:
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
            raise serializers.ValidationError("Token does not match for this invite")

        return unsigned_value

    def invalidate_invite(self, instance):
        """
        Invalidate the invite by deleting it
        """
        instance.invitation.delete(keep_parents=True)

    def change_membership_to_accepted(self, instance):
        """
        The function deletes the invitation, but keeps the membership that is connected to this.
                It creates a userprofile for the membership
                    This can only be done by authenticated users
        """
        self.invalidate_invite(instance)
        userprofile = UserProfile()
        userprofile.membership_ptr = instance
        instance.object_type = "WS"
        userprofile.save_base(raw=True)
        instance.user = self._context["request"].user

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

        self.validate_token_set(data)
        self.validate_email_is_unique(data)
        self.validate_user_in_membership(data)

        return data

    def validate_token_set(self, data):
        """
        Happens in PATCH action
        When the `status` field is set, make sure we validate the following:
        - Given token is valid and invitation is not consumed yet
        - Given token is invalid and report error
        - No token is given
        - Invite is already expired as in used already
        """
        if "status" in data:
            if (
                data["status"] == "accepted"
                and self.get_status(self.instance) == "invited"
            ):
                if "token" not in data:
                    raise serializers.ValidationError(
                        {"token": ["Token is required when accepting invitation"]}
                    )
            elif (
                data["status"] == "accepted"
                and self.get_status(self.instance) == "accepted"
            ):
                raise serializers.ValidationError({"token": ["Token is already used"]})

    def validate_email_is_unique(self, data):
        """
        This function validates whether the email is unique for the membership.
        If the email already exist it raises a ValidationError.

        # FIXME: change this when multiple memberships are possible (e.g. expired ones and new memberships)
        """
        if "email" in data:
            email = data["email"]
            membership = data["object_uuid"]

            if (
                Membership.objects.filter(
                    Q(invitation__email=email) | Q(user__email=email)
                )
                .filter(object_uuid=membership)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"email": ["This email already belongs to this workspace"]}
                )

    def validate_user_in_membership(self, data):
        """
        This function validates whether the user is unique for the membership.
        If the user is already part of the membership it raises an ValidationError.
        Also invalidate the invite immediately
        """
        if "status" in data:
            if (
                data["status"] == "accepted"
                and self.get_status(self.instance) == "invited"
            ):
                user = self._context["request"].user
                workspace = self.instance
                if (
                    Membership.objects.filter(Q(user=user))
                    .filter(object_uuid=workspace.uuid)
                    .exists()
                ):
                    self.invalidate_invite(self.instance)
                    raise serializers.ValidationError(
                        {"user": ["User is already part of this workspace"]}
                    )

    def update(self, instance, validated_data):
        """
        This function does the following:
            1. if the request changes the status to accepted when the initial status is invited and there exists a token,
                the change_membership_to_accepted function is called
            2. It updates the fields that are given in the validated_data and reloads model values from the database
        """
        status = validated_data.get("status", None)
        if (
            status == "accepted"
            and self.get_status(instance) == "invited"
            and self.generate_token()
        ):
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
        if not self.instance or self.get_status(self.instance) == "accepted":
            del fields["token"]

        if self.instance:
            fields["email"].read_only = True
            fields["object_uuid"].read_only = True
            # fields["object_type"].read_only = True

        return fields
