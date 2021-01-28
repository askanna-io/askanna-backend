import copy
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.db.models import Q
from rest_framework import serializers


from users.models import (
    User,
    UserProfile,
)
from users.signals import (
    user_created_signal,
    password_changed_signal,
    email_changed_signal,
)


class UserSerializer(serializers.ModelSerializer):
    """
    This UserSerializer is used to display information about the user
    Is also used to "show" the user profile of the user (general)
    """

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


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    This update serializer updates specific fields of the User model
    """

    old_password = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    short_uuid = serializers.CharField(required=False, read_only=True)

    def validate(self, data):
        """
        We validate additionally
        - when password is set, then old_password should also be set
        """
        data = super().validate(data)
        if data.get("password") and not data.get("old_password"):
            raise serializers.ValidationError(
                "To change your password, you also need to provide the current password."
            )
        return data

    def validate_email(self, value):
        """This function validates if the email is unique within our system
        Exclude our own user as this will return a positive hit"""
        email = value

        # first validate the e-mail whether this is valid or not
        validate_email(email)

        # then do a lookup in the database
        if User.objects.filter(Q(email=email)).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already used.")
        return value

    def validate_password(self, value):
        """This function validates if the password is longer than 10 characters.
        If not, a ValidationError is raised"""

        if len(value) < 10:
            raise serializers.ValidationError(
                "The password should be longer than 10 characters."
            )

        validate_password(value, user=self.instance)
        return value

    def validate_old_password(self, value):
        """
        Let's check whether the user setting the new password also knows the old password
        """
        user = authenticate(username=self.instance.username, password=value)
        if user is None:
            raise serializers.ValidationError("The current password is incorrect.")

        return value

    def update(self, instance, validated_data):
        email_changed = instance.email != validated_data.get("email", instance.email)
        old_email = copy.copy(instance.email)
        instance.email = validated_data.get("email", instance.email)
        instance.username = instance.email

        instance.name = validated_data.get("name", instance.name)
        # update password?
        # at this point, we should also have an validated `old_password`
        if validated_data.get("password") and validated_data.get("old_password"):
            instance.set_password(validated_data.get("password"))
        instance.save()

        request = self.context.get("request")
        # after save, trigger signals to send e-mail or notifications
        if validated_data.get("password"):
            password_changed_signal.send(
                sender=self.__class__, request=request, user=instance,
            )
        if email_changed:
            email_changed_signal.send(
                sender=self.__class__,
                request=request,
                user=instance,
                old_email=old_email,
            )
        return instance

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password",
            "old_password",
            "short_uuid",
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
