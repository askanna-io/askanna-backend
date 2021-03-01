from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.db.models import Model, Q
from django.template.loader import render_to_string

from rest_framework import serializers
from users.models import (
    MEMBERSHIPS,
    MSP_WORKSPACE,
    ROLES,
    WS_MEMBER,
    Invitation,
    Membership,
    UserProfile,
)
from workspace.models import Workspace


class ReadWriteSerializerMethodField(serializers.Field):
    """
    Code taken from: https://stackoverflow.com/questions/40555472/django-rest-serializer-method-writable-field?rq=1
    FIXME: to document what it does
    """

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


class PersonSerializer(serializers.Serializer):
    name = ReadWriteSerializerMethodField("get_name", required=False)
    status = ReadWriteSerializerMethodField("get_status", required=False)
    email = ReadWriteSerializerMethodField("get_email")
    uuid = serializers.UUIDField(read_only=True)
    short_uuid = serializers.CharField(read_only=True)
    object_uuid = serializers.UUIDField()
    object_type = serializers.ChoiceField(choices=MEMBERSHIPS, default=MSP_WORKSPACE)
    workspace = serializers.SerializerMethodField("get_workspace")
    role = serializers.ChoiceField(choices=ROLES, default=WS_MEMBER)
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    user = serializers.SerializerMethodField("get_user")
    avatar = serializers.SerializerMethodField("get_avatar")
    token = serializers.CharField(write_only=True)
    front_end_url = serializers.URLField(
        required=False, default=settings.ASKANNA_UI_URL
    )

    token_signer = signing.TimestampSigner()

    def generate_token(self, instance=None):
        """
        This function returns the token with as value the uuid of the instance
        """
        instance = instance or self.instance
        return self.token_signer.sign(instance.uuid)

    def get_workspace(self, instance):
        """
        object_type=WS
        object_uuid=uuid to Workspace
        """
        workspace = Workspace.objects.get(uuid=instance.object_uuid)
        return workspace.relation_to_json

    def get_user(self, instance):
        """
        We need to return the user relation, but with avatar
        extract from current instance and add this to the user relation serialization

        """
        if instance.user:
            return instance.user.relation_to_json
        return {
            "uuid": None,
            "short_uuid": None,
            "name": None,
        }

    def get_avatar(self, instance):
        """
        Return avatar only for this membership
        """
        membership_rel = instance.relation_to_json_with_avatar
        return membership_rel["avatar"]

    def get_name(self, instance):
        """
        This function gets the name from the user.
        """
        if not instance.name and instance.user:
            return instance.user.get_name()
        return instance.name

    def get_email(self, instance):
        """
        This function checks if there already exist an invitation.
        If it does then it uses the email from the invitation, otherwise it uses the email of the user.
        """
        if instance.user:
            return instance.user.email

        try:
            instance.invitation
        except Invitation.DoesNotExist:
            return None
        else:
            return instance.invitation.email

    @staticmethod
    def get_status(instance):
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

        if value not in [{"status": "accepted"}, {"status": "invited"}]:
            raise serializers.ValidationError("Invalid status")

        return value

    def validate_token(self, value):
        """
        This function validates the token and raises a validation error in the following cases:
            1. If the max_age of the token passed
            2. If the token passed doesn't match the actual token
        """
        try:
            unsigned_value = self.token_signer.unsign(
                value, max_age=timedelta(hours=settings.ASKANNA_INVITATION_VALID_HOURS)
            )
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
        print(instance.created, instance.modified)
        instance.object_type = MSP_WORKSPACE
        userprofile.save_base(raw=True)
        instance.user = self._context["request"].user

    def create(self, validated_data):
        """
        This function creates the Invitation
        """
        instance = Invitation.objects.create(**validated_data)
        self.send_invite(instance=instance)
        return instance

    def validate(self, data):
        """
        The token is needed to be able to accept the invitation.
        This function validates the data by checking if there exists a token and the status is accepted.
        """
        data = super().validate(data)

        self.validate_token_usage(data)
        self.validate_email_is_unique(data)
        self.validate_user_in_membership(data)

        return data

    def validate_token_usage(self, data):
        """
        Happens in PATCH action
        When the `status` field is set, make sure we validate the following:
        - Given token is valid and invitation is not consumed yet
        - Given token is invalid and report error
        - No token is given
        - Invite is already expired as in used already
        """
        if "status" in data and data["status"] == "accepted":
            if self.get_status(self.instance) == "invited" and "token" not in data:
                raise serializers.ValidationError(
                    {"token": ["Token is required when accepting invitation"]}
                )

            elif self.get_status(self.instance) == "accepted":
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
                    Q(invitation__email=email)
                    | (Q(user__email=email, deleted__isnull=True))
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
                if (
                    Membership.members.members()
                    .filter(Q(user=user))
                    .filter(object_uuid=self.instance.object_uuid)
                    .exists()
                ):
                    self.invalidate_invite(self.instance)
                    raise serializers.ValidationError(
                        {"user": ["User is already part of this workspace"]}
                    )

    def update(self, instance, validated_data):
        """
        This function does the following:
            1. if the request changes the status to accepted when the initial status is invited and
               there exists a token, the change_membership_to_accepted function is called
            2. It updates the fields that are given in the validated_data and reloads model values from the database
        """
        status = validated_data.get("status", None)
        if status == "accepted" and self.get_status(instance) == "invited":
            self.change_membership_to_accepted(instance)

        if status == "invited":
            # only resend invite if it was requested
            self.send_invite()

        for field, value in validated_data.items():
            print(field, value)
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
            fields["object_type"].read_only = True

        return fields

    def send_invite(self, instance=None):
        """This function generates the token when the invitation is send.
        A mail is sent to the email that is given as input when creating the invitation """
        instance = instance or self.instance
        token = self.generate_token(instance)
        workspace_uuid = instance.object_uuid
        workspace = Workspace.objects.get(uuid=workspace_uuid)

        data = {
            "token": token,
            "workspace_name": workspace,
            "workspace_short_uuid": workspace.short_uuid,
            "web_ui_url": instance.invitation.front_end_url.rstrip("/"),
            "people_short_uuid": instance.short_uuid,
        }

        subject = f"You’re invited to join {workspace} on AskAnna"
        from_email = settings.EMAIL_INVITATION_FROM_EMAIL

        text_version = render_to_string("emails/invitation_email.txt", data)
        html_version = render_to_string("emails/invitation_email.html", data)

        msg = EmailMultiAlternatives(
            subject, text_version, from_email, [instance.invitation.email]
        )
        msg.attach_alternative(html_version, "text/html")
        msg.send()
