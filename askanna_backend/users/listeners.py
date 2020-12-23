import json
import socket

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import loader

from users.models import PasswordResetLog, Membership, MSP_WORKSPACE, WS_ADMIN, User, UserProfile
from users.signals import password_reset_signal, user_created_signal
from workspace.models import Workspace


def visitor_ip_address(request):

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@receiver(password_reset_signal)
def handle_log_password_reset(sender, signal, users, request, domain, email, **kwargs):
    """
    After a password reset, log this action to keep track of who and when requested this
    """

    # logic to log
    remote_ip = visitor_ip_address(request)
    request_meta = dict(request.headers)
    hostname, aliaslist, ipddrlist = socket.gethostbyaddr(remote_ip)

    # create logentry for an password reset attempt
    for idx, user in enumerate(users):
        prl = PasswordResetLog.objects.create(
            email=email,
            user=user,
            remote_ip=remote_ip,
            remote_host=hostname,
            front_end_domain=domain,
            meta=request_meta,
        )

    # fix the case where we couldn't lookup a user for the e-mail
    # but still interesting to see if there was an attempt to reset
    # for a specific e-mailaddress
    if not users:
        prl = PasswordResetLog.objects.create(
            email=email,
            user=None,
            remote_ip=remote_ip,
            remote_host=hostname,
            front_end_domain=domain,
            meta=request_meta,
        )


@receiver(user_created_signal)
def create_workspace_after_signup(sender, user, request, workspace_name, **kwargs):
    """
    Create a workspace after the user is created
    When workspace_name is not given, then do not create a workspace for the new user
    """
    if workspace_name:
        workspace = Workspace.objects.create(title=workspace_name)

        membership = Membership.objects.create(
            object_uuid=workspace.uuid,
            object_type=MSP_WORKSPACE,
            role=WS_ADMIN,
            job_title="",
            user=user,
        )

        # also create a UserProfile for this membership
        userprofile = UserProfile()
        userprofile.membership_ptr = membership
        userprofile.save_base(raw=True)


@receiver(user_created_signal)
def send_welcome_email_after_registration(
    sender, user, request, workspace_name, **kwargs
):
    """
    After an user account is created, we send a welcome e-mail
    """

    subject_template_name = "emails/signup_welcome_subject.txt"
    email_template_name = "emails/signup_welcome_email.txt"
    html_email_template_name = "emails/signup_welcome_email.html"
    from_email = "AskAnna <support@askanna.io>"
    to_email = "{} <{}>".format(user.name, user.email)

    context = {
        "user": user,
    }

    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, "text/html")

    # add the attachments
    terms_of_use_dir = settings.RESOURCES_DIR.path("terms_and_conditions")
    attachments = [
        terms_of_use_dir.path(
            "European Model Form for Withdrawal - AskAnna - 20201202.pdf"
        ),
        terms_of_use_dir.path("Terms of Use - AskAnna - 20201202.pdf"),
        terms_of_use_dir.path("Data Processing Agreement - AskAnna - 20201214.pdf"),
    ]

    for attachment in attachments:
        email_message.attach_file(attachment)

    email_message.send()
