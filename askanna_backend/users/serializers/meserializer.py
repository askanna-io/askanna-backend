# -*- coding: utf-8 -*-
from typing import Dict
from rest_framework import serializers

from users.models import (
    Membership,
    User,
    UserProfile,
)
from .personserializer import PersonSerializer
from .profileimageserializer import ProfileImageSerializer


class BaseMeSerializer(serializers.ModelSerializer):
    uuid = serializers.SerializerMethodField("get_uuid")
    short_uuid = serializers.SerializerMethodField("get_short_uuid")
    name = serializers.SerializerMethodField("get_name")
    job_title = serializers.SerializerMethodField("get_job_title")
    email = serializers.SerializerMethodField("get_email")

    role = serializers.SerializerMethodField("get_role")
    membership = serializers.SerializerMethodField("get_membership")
    permission = serializers.SerializerMethodField("get_permission")
    avatar = serializers.SerializerMethodField("get_avatar")

    @property
    def is_member(self) -> bool:
        """
        Helper function to determine the no-member role from both Membership and User model
        A non-member doesn't have the uuid and short_uuid set
        """
        if isinstance(self.instance, Membership) and getattr(self.instance, "user"):
            return True

        if isinstance(self.instance, User) and getattr(self.instance, "uuid"):
            return True
        return False

    def get_uuid(self, instance):
        if self.is_member:
            return instance.uuid
        return None

    def get_short_uuid(self, instance):
        if self.is_member:
            return instance.short_uuid
        return None

    def get_name(self, instance):
        if self.is_member:
            return instance.name
        return "Guest"

    def get_job_title(self, instance):
        if self.is_member:
            return instance.job_title
        return "Guest"

    def get_email(self, instance):
        if self.is_member:
            return instance.email
        return None

    def get_role(self, instance):
        role = self.context["request"].role
        user_roles = self.context["request"].user_roles
        if len(user_roles) > 1:
            role = user_roles[1]  # the second one is the role on this object
        return {
            "name": role.name,
            "code": role.code,
        }

    def get_membership(self, instance):
        return None

    def _get_true_permissions(self, permissions: Dict) -> Dict:
        return dict(filter(lambda x: x[1] is True, permissions.items()))

    def get_permission(self, instance):
        permissions = []
        role = self.context["request"].role
        object_roles = self.context["request"].user_roles
        if not role and not object_roles:
            return []
        permissions = role.full_permissions(role)
        true_permissions = self._get_true_permissions(permissions)

        for role in object_roles:
            # filter out `false` permissions, we don't want to override permissions already given as True
            role_permissions = role.full_permissions(role)
            role_true_permissions = self._get_true_permissions(role_permissions)
            true_permissions.update(**role_true_permissions)
            permissions.update(**role_permissions)
            permissions.update(**true_permissions)

        return permissions

    def get_avatar(self, instance):
        if self.is_member:
            return instance.avatar_cdn_locations()
        return {}

    class Meta:
        model = User
        fields = (
            "uuid",
            "short_uuid",
            "name",
            "email",
            "job_title",
            "role",
            "membership",
            "permission",
            "avatar",
        )


class UpdateMeSerializer(BaseMeSerializer):
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    job_title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """
        Only allow certain fields to be updated
        """
        instance.name = validated_data.get("name", instance.name)
        instance.job_title = validated_data.get("job_title", instance.job_title)
        instance.save(update_fields=["name", "job_title", "modified"])
        return instance


class GlobalMeSerializer(BaseMeSerializer):
    def get_permission(self, instance):
        permissions = super().get_permission(instance)
        global_permissions = dict(filter(lambda x: x[0].startswith("askanna"), permissions.items()))
        return global_permissions


class ObjectMeSerializer(BaseMeSerializer):
    def get_membership(self, instance):
        return PersonSerializer(instance=self.context.get("request").membership, many=False).data

    def get_email(self, instance):
        if self.is_member:
            return instance.user.email
        return None

    class Meta:
        model = UserProfile
        fields = (
            "uuid",
            "short_uuid",
            "name",
            "email",
            "job_title",
            "role",
            "membership",
            "permission",
            "avatar",
            "use_global_profile",
        )


class WorkspaceMeSerializer(ObjectMeSerializer):
    def get_permission(self, instance):
        permissions = super().get_permission(instance)
        global_permissions = dict(filter(lambda x: x[0].startswith("askanna"), permissions.items()))
        workspace_permissions = dict(filter(lambda x: x[0].startswith("workspace"), permissions.items()))
        global_permissions.update(**workspace_permissions)
        return global_permissions


class ProjectMeSerializer(ObjectMeSerializer):
    def get_permission(self, instance):
        permissions = super().get_permission(instance)
        return permissions


class UpdateObjectMeSerializer(ObjectMeSerializer):
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    job_title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def get_membership(self, instance):
        """
        This feels a bit recursive, but we just need the PersonSerializer for the nested info
        """
        return PersonSerializer(instance=instance, many=False).data

    def update(self, instance, validated_data):
        """
        Only allow certain fields to be updated
        """
        instance.name = validated_data.get("name", instance.name)
        instance.job_title = validated_data.get("job_title", instance.job_title)
        instance.use_global_profile = validated_data.get("use_global_profile", instance.use_global_profile)
        instance.save(update_fields=["name", "job_title", "use_global_profile", "modified"])
        instance.refresh_from_db()
        return instance


class AvatarMeSerializer(ProfileImageSerializer):
    class Meta:
        model = User
        fields = [
            "avatar",
            "short_uuid",
        ]


class ObjectAvatarMeSerializer(ProfileImageSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "avatar",
            "short_uuid",
        ]
