from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from account.models.membership import ROLES, Invitation, Membership
from account.serializers.user import RoleSerializer
from core.permissions.askanna_roles import get_role_class
from core.utils.config import get_setting
from storage.serializers import FileDownloadInfoSerializer
from workspace.serializers import WorkspaceRelationSerializer


def is_email_active_in_object_membership(email: str, object_uuid: str) -> bool:
    """Check if email is already linked to an active membership for an object

    This function validates whether the email is not linked to an active membership for the object. If the email
    already exist it returns True, else it return False.

    Args:
        email (str): Email to check
        object_uuid (str): Object UUID to check

    Returns:
        bool: True if email is already linked to an active membership for the object, else False
    """

    return (
        Membership.objects.filter(
            Q(invitation__email__iexact=email) | (Q(user__email__iexact=email, deleted_at__isnull=True))
        )
        .filter(object_uuid=object_uuid)
        .exists()
    )


def validate_invite_status(instance):
    if instance.status == "active":
        raise serializers.ValidationError({"detail": "Invitation is already accepted"})
    if instance.status == "deleted":
        raise serializers.ValidationError({"detail": "Invitation is deleted"})
    if instance.status == "blocked":
        raise serializers.ValidationError({"detail": "Invitation is blocked"})


def send_invite(instance, front_end_url):
    data = {
        "token": instance.invitation.generate_token(),
        "workspace_name": instance.workspace.name,
        "workspace_suuid": instance.workspace.suuid,
        "web_ui_url": front_end_url.rstrip("/"),
        "people_suuid": instance.suuid,
    }

    subject = f"You’re invited to join {instance.workspace.name} on AskAnna"
    from_email = settings.EMAIL_INVITATION_FROM_EMAIL

    text_version = render_to_string("emails/invitation_email.txt", data)
    html_version = render_to_string("emails/invitation_email.html", data)

    msg = EmailMultiAlternatives(subject, text_version, from_email, [instance.invitation.email])
    msg.attach_alternative(html_version, "text/html")
    msg.send()


class PeopleSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    name = serializers.CharField(source="member_name")
    job_title = serializers.CharField(source="member_job_title", required=False)
    avatar = serializers.ImageField(
        default=None,
        allow_null=True,
        write_only=True,
        help_text=(
            "Upload an image file that will be used as the authenticated user's avatar. Existing image files are "
            "automatically deleted. Submit the avatar field with an empty value to delete an existing image file "
            "without uploading a new one."
        ),
    )
    avatar_file = FileDownloadInfoSerializer(read_only=True, source="get_avatar_file")
    workspace = WorkspaceRelationSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    role_code = serializers.ChoiceField(write_only=True, required=False, choices=ROLES)

    @extend_schema_field(RoleSerializer)
    def get_role(self, instance):
        return RoleSerializer(get_role_class(instance.role)).data

    def update(self, instance, validated_data):
        if "member_name" in validated_data.keys():
            instance.name = validated_data["member_name"]
            instance.member_name = validated_data["member_name"]

            instance.use_global_profile = False

        if "member_job_title" in validated_data.keys():
            instance.job_title = validated_data["member_job_title"]
            instance.member_job_title = validated_data["member_job_title"]

            if not instance.name:
                instance.name = instance.member_name

            instance.use_global_profile = False

        if "role_code" in validated_data.keys():
            instance.role = validated_data["role_code"]

        if "avatar" in validated_data.keys():
            instance.use_global_profile = False
            avatar_file = validated_data.pop("avatar")
            if avatar_file is not None:
                instance.set_avatar(
                    avatar_file,
                    created_by=Membership.objects.get(
                        user=self.context["request"].user, object_uuid=instance.object_uuid
                    ),
                )
            else:
                instance.delete_avatar_file()

        instance.save(
            update_fields=[
                "use_global_profile",
                "name",
                "job_title",
                "role",
                "modified_at",
            ]
        )
        return instance

    class Meta:
        model = Membership
        fields = (
            "suuid",
            "status",
            "name",
            "job_title",
            "avatar",
            "avatar_file",
            "workspace",
            "role",
            "role_code",
        )


class InviteSerializer(serializers.Serializer):
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=True)
    job_title = serializers.CharField(required=False)
    role = RoleSerializer(read_only=True, source="get_role")
    role_code = serializers.ChoiceField(write_only=True, required=False, choices=ROLES)
    workspace = WorkspaceRelationSerializer(read_only=True)
    front_end_url = serializers.URLField(write_only=True, required=False)

    def validate(self, data=None):
        if data:
            data["object_uuid"] = self.initial_data.get("object_uuid")
            data["object_type"] = self.initial_data.get("object_type")
            self.validate_email_is_not_active_in_object(data["email"], data["object_uuid"])
            self.validate_member_invite_admin(data)

        return data

    def validate_email_is_not_active_in_object(self, email: str, object_uuid: str):
        if is_email_active_in_object_membership(email, object_uuid):
            raise serializers.ValidationError(
                {"email": [f"The email {email} already has a membership or invitation for this workspace."]}
            )

    def validate_member_invite_admin(self, data):
        """
        Only workspace admins are allowed to invite admins. Raises ValidationError when a member tries to invite an
        admin to the workspace.
        """
        role_for_invite = data.get("role_code")

        if not role_for_invite or (role_for_invite and role_for_invite != "WA"):
            return

        current_user_role = Membership.objects.get(
            object_type=data["object_type"],
            object_uuid=data["object_uuid"],
            user=self.context.get("request").user,
            deleted_at__isnull=True,
        )
        if current_user_role.role != "WA":
            raise serializers.ValidationError({"role": ["You are not allowed to set an invite role to admin."]})

    def create(self, validated_data):
        if "role_code" in validated_data:
            validated_data["role"] = validated_data.pop("role_code")

        front_end_url = validated_data.pop("front_end_url", get_setting("ASKANNA_UI_URL"))

        self.instance = Invitation.objects.create(**validated_data)
        send_invite(self.instance, front_end_url)
        return self.instance


class InviteCheckEmail(serializers.Serializer):
    email_exist = serializers.ListField(child=serializers.EmailField(), read_only=True, default=None, allow_null=True)

    def validate(self, data):
        request = self.context["request"]

        email_exist = []
        for email_param in request.query_params.getlist("email"):
            for email in email_param.split(","):
                if is_email_active_in_object_membership(email=email, object_uuid=self.initial_data.get("object_uuid")):
                    email_exist.append(email)

        data["email_exist"] = email_exist if email_exist else None
        return data


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        data = super().validate(data)
        validate_invite_status(self.instance)
        self.validate_user_in_membership()
        return data

    def validate_token(self, value):
        """
        This function validates the token and raises a validation error in the following cases:
            1. If the invitation related to the token is not found
            2. If the max_age of the token passed
            3. If the token passed doesn't match the actual token
        """
        try:
            unsigned_value = self.instance.invitation.token_signer.unsign(
                value, max_age=timedelta(hours=settings.ASKANNA_INVITATION_VALID_HOURS)
            )
        except Membership.invitation.RelatedObjectDoesNotExist as exc:
            raise serializers.ValidationError("Token is not valid") from exc
        except signing.SignatureExpired as exc:
            raise serializers.ValidationError("Token expired") from exc
        except signing.BadSignature as exc:
            raise serializers.ValidationError("Token is not valid") from exc
        if str(self.instance.suuid) != unsigned_value:
            raise serializers.ValidationError("Token is not valid")

        return unsigned_value

    def validate_user_in_membership(self):
        """
        This function validates whether the user who does the request to accept the invitation, is not already a member
        of the workspace.
        """
        user = self.context["request"].user
        if (
            Membership.objects.active_members()
            .filter(
                user=user,
                object_uuid=self.instance.object_uuid,
                deleted_at__isnull=True,
            )
            .exists()
        ):
            raise serializers.ValidationError({"detail": "Account is already member of this workspace"})

    def set_membership_to_accepted(self):
        """
        Delete the invitation, but keep the membership that is connected to this.
        Also, set the user to the user who does the request to accept the invite.
        """

        self.instance.invitation.delete(keep_parents=True)
        self.instance.user = self._context["request"].user
        self.instance.save()


class InviteInfoSerializer(AcceptInviteSerializer):
    suuid = serializers.CharField(read_only=True)
    status = serializers.CharField(source="get_status", read_only=True)
    email = serializers.EmailField(read_only=True)
    role = RoleSerializer(source="get_role")
    workspace = WorkspaceRelationSerializer(read_only=True)


class ResendInviteSerializer(serializers.Serializer):
    front_end_url = serializers.URLField(required=False)
