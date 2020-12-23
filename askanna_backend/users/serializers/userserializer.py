from django.conf import settings

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.forms import PasswordResetForm
from users.models import (
    User,
    UserProfile,
)
from users.signals import password_reset_signal, user_created_signal
from workspace.models import Workspace


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "short_uuid",
            "is_active",
            "date_joined",
            "last_login",
        ]


class UserCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    workspace = serializers.CharField(write_only=True, required=False)
    terms_of_use = serializers.BooleanField(write_only=True, required=True)
    short_uuid = serializers.CharField(required=False, read_only=True)

    front_end_domain = serializers.CharField(
        required=False, default=settings.ASKANNA_UI_URL
    )

    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        """
        This function creates an user account and set the password
        """
        workspace_name = validated_data.pop("workspace", None)
        tou = validated_data.pop("terms_of_use")
        password = validated_data.pop("password")
        # hard code to set the username to e-mail
        validated_data["username"] = validated_data.get("email")

        domain = validated_data.get("front_end_domain", "")
        domain = domain.replace("https://", "").replace("http://", "")
        validated_data["front_end_domain"] = domain.rstrip("/")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # create the workspace for the user, use a signal to do this in a downstream process
        request = self.context.get("request")
        # log the password reset request
        user_created_signal.send(
            sender=self.__class__,
            request=request,
            user=user,
            workspace_name=workspace_name,
        )
        return user

    def validate(self, data):
        """
        This function validates the data
        """
        data = super().validate(data)
        self.validate_password_not_similar_username(data)

        return data

    def validate_email(self, value):
        """This function validates if the email is unique within our system"""
        email = value
        if User.objects.filter(Q(email=email)).exists():
            raise serializers.ValidationError("This email is already used.")
        return value

    def validate_password(self, value):
        """This function validates if the password is longer than 10 characters.
        If not, a ValidationError is raised"""

        if len(value) < 10:
            raise serializers.ValidationError(
                "The password should be longer than 10 characters."
            )
        return value

    def validate_password_not_similar_username(self, data):
        """This function validates if the password is not similar to the username.
        If this is the case, a ValidationError is raised"""

        if data.get("username") and data.get("password"):
            if data.get("username") in data.get("password"):
                raise serializers.ValidationError(
                    "The password should not be similar to the username"
                )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"

