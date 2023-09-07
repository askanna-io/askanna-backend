from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from account.models.membership import Membership
from account.models.user import User
from account.serializers.user import AvatarSerializer, RoleSerializer
from core.permissions.askanna_roles import (
    get_request_role,
    get_role_class,
    merge_role_permissions,
)
from core.serializers import ReadWriteSerializerMethodField


class MeSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(default=None)
    email = serializers.EmailField(read_only=True)
    job_title = serializers.CharField(allow_blank=True, default=None)
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
    avatar_files = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField(read_only=True)
    permission = serializers.SerializerMethodField()

    @extend_schema_field(RoleSerializer)
    def get_role(self, instance):
        role = get_request_role(self.context["request"])
        return RoleSerializer(role).data

    @extend_schema_field(AvatarSerializer)
    def get_avatar_files(self, instance):
        if self.context["request"].user.is_anonymous:
            return None

        if hasattr(instance, "get_avatar_files"):
            avatar_files = instance.get_avatar_files()
        else:
            avatar_files = instance.avatar_files

        if avatar_files:
            return AvatarSerializer(avatar_files, context=self.context).data

        return None

    def get_permission(self, instance) -> dict[str, bool]:
        user_roles = self.context["request"].user_roles
        return merge_role_permissions(user_roles)

    def update(self, instance, validated_data):
        if "avatar" in validated_data.keys():
            avatar_file = validated_data.pop("avatar")
            if avatar_file is not None:
                instance.set_avatar(avatar_file)
            else:
                instance.delete_avatar_files()

        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = (
            "suuid",
            "name",
            "email",
            "job_title",
            "avatar",
            "avatar_files",
            "role",
            "permission",
        )


class MembershipMeSerializer(MeSerializer):
    name = ReadWriteSerializerMethodField(required=True)
    email = serializers.SerializerMethodField()
    job_title = ReadWriteSerializerMethodField(required=False)

    def get_name(self, instance) -> str | None:
        if self.context["request"].user.is_anonymous:
            return None
        return instance.get_name()

    def get_email(self, instance) -> str | None:
        if self.context["request"].user.is_anonymous:
            return None
        return self.context["request"].user.email

    def get_job_title(self, instance) -> str | None:
        if self.context["request"].user.is_anonymous:
            return None
        return instance.get_job_title()

    @extend_schema_field(RoleSerializer)
    def get_role(self, instance):
        role = get_role_class(instance.role)
        return RoleSerializer(role).data

    def update(self, instance, validated_data):
        # We update a Membership instance. To serve the right information, we make sure that we use the membership
        # profile instead of the global profile.
        if "use_global_profile" not in validated_data.keys():
            instance.use_global_profile = False

        return super().update(instance, validated_data)

    class Meta:
        model = Membership
        fields = (
            "suuid",
            "name",
            "email",
            "job_title",
            "avatar",
            "avatar_files",
            "use_global_profile",
            "role",
            "permission",
        )
