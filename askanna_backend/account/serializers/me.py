import base64
import binascii
import io

from account.models import User, UserProfile
from core.permissions.askanna_roles import get_role_class, merge_role_permissions
from core.serializers import ReadWriteSerializerMethodField
from drf_spectacular.utils import extend_schema_field
from PIL import Image
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from .user import RoleSerializer


class MeSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True, allow_null=True, default=None)
    name = serializers.CharField(default=None)
    email = serializers.EmailField(read_only=True, default=None)
    job_title = serializers.CharField(allow_blank=True, default=None)
    avatar = serializers.DictField(read_only=True, allow_null=True, default=None, source="avatar_cdn_locations")
    role = serializers.SerializerMethodField("get_role")
    permission = serializers.SerializerMethodField("get_permission")

    @extend_schema_field(RoleSerializer)
    def get_role(self, instance):
        role = User.get_role(self.context["request"])
        return RoleSerializer(role).data

    def get_permission(self, instance) -> dict[str, bool]:
        user_roles = self.context["request"].user_roles
        return merge_role_permissions(user_roles)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.job_title = validated_data.get("job_title", instance.job_title)
        instance.save(
            update_fields=[
                "name",
                "job_title",
                "modified_at",
            ]
        )
        return instance

    class Meta:
        model = User
        fields = (
            "suuid",
            "name",
            "email",
            "job_title",
            "avatar",
            "role",
            "permission",
        )


class ObjectMeSerializer(MeSerializer):
    name = ReadWriteSerializerMethodField("get_name", required=True)
    email = serializers.SerializerMethodField()
    job_title = ReadWriteSerializerMethodField("get_job_title", required=False)
    avatar = serializers.SerializerMethodField()

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

    def get_avatar(self, instance) -> dict[str, str] | None:
        if self.context["request"].user.is_anonymous:
            return None
        return instance.get_avatar()

    @extend_schema_field(RoleSerializer)
    def get_role(self, instance):
        role = get_role_class(instance.role)
        return RoleSerializer(role).data

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.job_title = validated_data.get("job_title", instance.job_title)
        instance.use_global_profile = validated_data.get("use_global_profile", instance.use_global_profile)
        instance.save(
            update_fields=[
                "name",
                "job_title",
                "use_global_profile",
                "modified_at",
            ]
        )
        return instance

    class Meta:
        model = UserProfile
        fields = (
            "suuid",
            "name",
            "email",
            "job_title",
            "avatar",
            "use_global_profile",
            "role",
            "permission",
        )


class WorkspaceMeSerializer(ObjectMeSerializer):
    ...


class ProjectMeSerializer(ObjectMeSerializer):
    ...


class AvatarSerializer(serializers.ModelSerializer):
    """
    The AvatarSerializer is used to validate the avatar and save it in relation to a UserProfile instance.
    """

    avatar = serializers.CharField(required=True, write_only=True)

    def validate_avatar(self, value):
        """
        Validate the content of the avatar, as this is a base64 encoded value, we need to validate whether this is
        an image or not
        """
        try:
            _, image_encoded = value.split(";base64,")
        except ValueError:
            raise ValidationError("Image is not valid. Is the avatar Base64 encoded?") from None

        try:
            image_binary = base64.standard_b64decode(image_encoded)
        except binascii.Error as exc:
            raise ValidationError(f"Image is not valid. Error received: {exc}") from exc

        try:
            Image.open(io.BytesIO(image_binary))
        except (TypeError, Exception) as exc:
            raise ValidationError(f"Image is not valid. Error received: {exc}") from exc

        return image_binary

    def save(self):
        """
        Perform save of the avatar if set self.validated_data.get('avatar')
        """
        if self.instance and self.validated_data:
            avatar = self.validated_data.get("avatar")
            if avatar:
                self.instance.write(io.BytesIO(avatar))
                self.instance.save(update_fields=["modified_at"])
        super().save()

    class Meta:
        model = UserProfile
        fields = ["avatar"]
        status = status.HTTP_204_NO_CONTENT


class MeAvatarSerializer(AvatarSerializer):
    "Serializer for the user's avatar"

    class Meta(AvatarSerializer.Meta):
        model = User


class WorkspaceMeAvatarSerializer(AvatarSerializer):
    "Serializer for workspace's member avatar"
    pass
