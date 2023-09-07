from copy import copy

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from rest_framework import serializers

from account.models.user import User
from account.signals import (
    email_changed_signal,
    password_changed_signal,
    user_created_signal,
)
from core.utils.config import get_setting


class AccountSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    is_active = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    workspace_name = serializers.CharField(write_only=True, required=False)
    terms_of_use = serializers.BooleanField(write_only=True, required=True)

    front_end_url = serializers.URLField(write_only=True, required=False)

    def create(self, validated_data):
        """
        This function creates an user account and set the password
        """
        # Hard code to set the username to e-mail
        validated_data["username"] = validated_data["email"]
        password = validated_data.pop("password")
        validated_data.pop("terms_of_use")  # Only needed for validation
        workspace_name = validated_data.pop("workspace_name", None)
        front_end_url = validated_data.pop("front_end_url", get_setting("ASKANNA_UI_URL"))

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Send signal to send welcome email and create the workspace if workspace_name is provided
        user_created_signal.send(
            sender=self.__class__,
            user=user,
            workspace_name=workspace_name,
            front_end_url=front_end_url,
        )

        return user

    def validate_email(self, value):
        """This function validates if the email is valid and unique within our system"""
        validate_email(value)

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already used.")

        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_terms_of_use(self, value):
        if value is not True:
            raise serializers.ValidationError("Please accept the terms of use.")
        return value

    class Meta:
        model = User
        fields = [
            "suuid",
            "name",
            "email",
            "password",
            "terms_of_use",
            "is_active",
            "date_joined",
            "last_login",
            "modified_at",
            "workspace_name",
            "front_end_url",
        ]


class AccountUpdateSerializer(serializers.ModelSerializer):
    """
    This update serializer updates specific fields of the User model
    """

    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=False)

    password = serializers.CharField(write_only=True, required=False)
    old_password = serializers.CharField(write_only=True, required=False)

    is_active = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    def update(self, instance, validated_data):
        name_changed = instance.name != validated_data.get("name", instance.name)
        if name_changed:
            instance.name = validated_data.get("name", instance.name)

        email_changed = instance.email != validated_data.get("email", instance.email)
        old_email = copy(instance.email)
        if email_changed:
            instance.email = validated_data.get("email", instance.email)
            instance.username = instance.email

        password_changed = validated_data.get("password") is not None
        if password_changed:
            instance.set_password(validated_data.get("password"))

        if name_changed or email_changed or password_changed:
            instance.save()

        # Trigger signals to send (e-mail) notifications when email or password is changed
        if email_changed:
            email_changed_signal.send(
                sender=self.__class__,
                user=instance,
                old_email=old_email,
            )
        if password_changed:
            password_changed_signal.send(
                sender=self.__class__,
                user=instance,
            )

        return instance

    def validate(self, data):
        """
        We validate additionally
        - when password is set, then old_password should also be set
        """
        data = super().validate(data)
        self.validate_update_password(data)
        return data

    def validate_email(self, value):
        """This function validates if the email is valid and unique within our system"""
        validate_email(value)

        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already used.")

        return value

    def validate_password(self, value):
        validate_password(value, user=self.instance)
        return value

    def validate_old_password(self, value):
        """
        Let's check whether the user setting the new password also knows the old password
        """
        user = authenticate(username=self.instance.username, password=value)
        if user is None:
            raise serializers.ValidationError("The old password is incorrect.")
        return value

    def validate_update_password(self, data):
        if data.get("password") and not data.get("old_password"):
            raise serializers.ValidationError(
                {"old_password": ["To change your password, you also need to provide the current password."]}
            )
        if data.get("password") and (data.get("password") == data.get("old_password")):
            raise serializers.ValidationError(
                {"password": ["The new password should be different from the old password."]}
            )

    class Meta:
        model = User
        fields = [
            "suuid",
            "name",
            "email",
            "password",
            "old_password",
            "is_active",
            "date_joined",
            "last_login",
            "modified_at",
        ]
