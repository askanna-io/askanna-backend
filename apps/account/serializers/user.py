from dj_rest_auth.serializers import (
    PasswordResetSerializer as DefaultPasswordResetSerializer,
)
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode as uid_decoder
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from account.models.membership import AVATAR_SPECS
from account.models.user import User
from account.signals import password_reset_signal
from core.utils.config import get_setting
from storage.serializers import FileDownloadInfoSerializer


class UserSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "suuid",
            "name",
            "email",
            "is_active",
            "date_joined",
            "last_login",
        ]


class RoleSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()


class AvatarSerializer(serializers.Serializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        if instance:
            instance = {
                avatar_file.name.split(".")[0]
                if avatar_file.name.split(".")[0] in AVATAR_SPECS
                else "original": avatar_file
                for avatar_file in instance
            }

        super().__init__(instance, data=data, **kwargs)

        self.fields["original"] = FileDownloadInfoSerializer()
        for spec_name in AVATAR_SPECS.keys():
            self.fields[spec_name] = FileDownloadInfoSerializer()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=True)
    password = serializers.CharField(required=True)

    def authenticate(self, **kwargs):
        return authenticate(self.context["request"], **kwargs)

    def get_auth_user(self, email, password):
        """
        'get_auth_user' returns the authenticated user instance if credentials are correct, else 'None'
        """
        try:
            username = User.objects.get(email__iexact=email).get_username()
        except User.DoesNotExist:
            return None
        else:
            return self.authenticate(username=username, password=password)

    @staticmethod
    def validate_auth_user_status(user):
        if not user.is_active:
            raise exceptions.ValidationError("This account is disabled.")

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = self.get_auth_user(email, password)

        if not user:
            raise exceptions.ValidationError("Unable to log in with provided credentials.")

        self.validate_auth_user_status(user)

        data["user"] = user
        return data


class PasswordResetSerializer(DefaultPasswordResetSerializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    front_end_url = serializers.URLField(required=False)

    def get_email_options(self) -> dict:
        return {"from_email": "AskAnna <support@askanna.io>"}

    def save(self):
        """
        We change the opts for sending the password reset e-mail. (AskAnna)
        """
        request = self.context.get("request")
        # Set some values to trigger the send_email method.

        front_end_url = self.validated_data.get("front_end_url", get_setting("ASKANNA_UI_URL"))
        domain = front_end_url.replace("https://", "").replace("http://", "").rstrip("/")
        is_secure = "https" in front_end_url

        opts = {
            "domain_override": domain,
            "use_https": is_secure,
            "request": request,
            "subject_template_name": "emails/password_reset_subject.txt",
            "email_template_name": "emails/password_reset_email.txt",
            "html_email_template_name": "emails/password_reset_email.html",
        }

        opts.update(self.get_email_options())
        self.reset_form.save(**opts)
        email = self.reset_form.cleaned_data["email"]
        users = list(self.reset_form.get_users(email))

        # Log the password reset request
        password_reset_signal.send(
            sender=self.__class__,
            request=request,
            domain=domain,
            users=users,
            email=email,
        )


class PasswordResetTokenStatusSerializer(serializers.Serializer):
    status = serializers.CharField(required=False, read_only=True)
    uid = serializers.CharField(required=False, write_only=True)
    token = serializers.CharField(required=False, write_only=True)

    def validate(self, data):
        try:
            uid = force_str(uid_decoder(data["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise ValidationError(
                {
                    "status": "invalid",
                    "uid": ["User UID value is invalid."],
                }
            ) from exc
        if not default_token_generator.check_token(user, data["token"]):
            raise ValidationError({"status": "invalid", "detail": ["The User UID and token combination is invalid."]})

        data["status"] = "valid"

        return data

    class Meta:
        fields = [
            "status",
            "uid",
            "token",
        ]