# -*- coding: utf-8 -*-
import socket

from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from PIL import Image

from core.mail import send_email
from users.models import (
    PasswordResetLog,
    Membership,
    MSP_WORKSPACE,
    WS_ADMIN,
    UserProfile,
    Invitation,
)
from users.signals import (
    password_reset_signal,
    user_created_signal,
    password_changed_signal,
    email_changed_signal,
    avatar_changed_signal,
)
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
        _ = PasswordResetLog.objects.create(
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
        _ = PasswordResetLog.objects.create(
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
        workspace = Workspace.objects.create(name=workspace_name)

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
    # add the attachments
    terms_of_use_dir = settings.RESOURCES_DIR.path("terms_and_conditions")
    attachments = [
        terms_of_use_dir.path(
            "European Model Form for Withdrawal - AskAnna - 20201202.pdf"
        ),
        terms_of_use_dir.path("Terms of Use - AskAnna - 20201202.pdf"),
        terms_of_use_dir.path("Data Processing Agreement - AskAnna - 20201214.pdf"),
    ]

    send_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        from_email,
        to_email,
        context,
        attachments,
    )


@receiver(email_changed_signal)
def send_email_changed(sender, user, request, old_email, **kwargs):
    """
    We send an e-mail to confirm the e-mail change
    """

    subject_template_name = "emails/email_changed_subject.txt"
    email_template_name = "emails/email_changed_email.txt"
    html_email_template_name = "emails/email_changed_email.html"
    from_email = "AskAnna <support@askanna.io>"
    to_email = "{} <{}>".format(user.name, old_email)

    context = {
        "user": user,
    }

    send_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        from_email,
        to_email,
        context,
    )


@receiver(password_changed_signal)
def send_password_changed(sender, user, request, **kwargs):
    """
    We send an e-mail to confirm the password change
    """

    subject_template_name = "emails/password_changed_subject.txt"
    email_template_name = "emails/password_changed_email.txt"
    html_email_template_name = "emails/password_changed_email.html"
    from_email = "AskAnna <support@askanna.io>"
    to_email = "{} <{}>".format(user.name, user.email)

    context = {
        "user": user,
    }

    send_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        from_email,
        to_email,
        context,
    )


@receiver(avatar_changed_signal)
def convert_avatars(sender, instance, **kwargs):
    """
    Upon writing a new avatar to the filesystem, we convert this avatar to several sizes and always save as PNG
    """
    userprofile = instance

    for spec_name, spec_size in userprofile.avatar_specs.items():
        filename = instance.stored_path_with_name(spec_name)
        with Image.open(userprofile.stored_path) as im:
            im.thumbnail(spec_size)
            im.save(filename, "png")


@receiver(pre_delete, sender=Membership)
def remove_membership(sender, instance, **kwargs):
    instance.prune()


@receiver(post_save, sender=UserProfile)
def install_avatar_after_new_membership(sender, instance, created, **kwargs):
    """
    Install a default avatar for the user when a profile was created
    """
    if created:
        instance.refresh_from_db()
        instance.install_default_avatar()


@receiver(post_save, sender=Invitation)
def install_avatar_after_new_invite(sender, instance, created, **kwargs):
    """
    Install a default avatar for the user when he was invited
    """
    if created:
        instance.refresh_from_db()
        instance.install_default_avatar()
