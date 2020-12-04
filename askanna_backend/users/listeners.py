import json
import socket

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver

from users.models import PasswordResetLog
from users.signals import password_reset_signal


def visitor_ip_address(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
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
            meta=request_meta
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
            meta=request_meta
        )
