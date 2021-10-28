from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode as uid_decoder
from rest_auth.serializers import (
    PasswordResetSerializer as DefaultPasswordResetSerializer,
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.forms import PasswordResetForm
from users.models import User
from users.signals import password_reset_signal


class PasswordResetSerializer(DefaultPasswordResetSerializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    front_end_domain = serializers.CharField(
        required=False, default=settings.ASKANNA_UI_URL
    )
    password_reset_form_class = PasswordResetForm

    def get_email_options(self) -> dict:
        return {"from_email": "AskAnna <support@askanna.io>"}

    def save(self):
        """
        We change the opts for sending the password reset e-mail. (AskAnna)
        """
        request = self.context.get("request")
        # Set some values to trigger the send_email method.

        domain = self.validated_data.get("front_end_domain", "")
        domain = domain.replace("https://", "").replace("http://", "")
        domain = domain.rstrip("/")
        is_secure = "https" in self.validated_data.get("front_end_domain", "")

        opts = {
            "domain_override": domain,
            "use_https": is_secure,
            "request": request,
            "subject_template_name": "registration/password_reset_subject.txt",
            "email_template_name": "registration/password_reset_email.txt",
            "html_email_template_name": "registration/password_reset_email.html",
        }

        opts.update(self.get_email_options())
        self.reset_form.save(**opts)
        email = self.reset_form.cleaned_data["email"]
        users = list(self.reset_form.get_users(email))

        # log the password reset request
        password_reset_signal.send(
            sender=self.__class__,
            request=request,
            domain=domain,
            users=users,
            email=email,
        )


class PasswordResetStatusSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    token = serializers.CharField(allow_blank=False)
    uid = serializers.CharField(allow_blank=False)

    def validate(self, attrs):
        self._errors = {}

        # Decode the uidb64 to uid to get User object
        try:
            uid = force_text(uid_decoder(attrs["uid"]))
            self.user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({"uid": ["Invalid value"], "status": "invalid"})

        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise ValidationError({"token": ["Invalid value"], "status": "invalid"})

        return attrs

    def to_representation(self, instance):
        return {"status": "valid"}
