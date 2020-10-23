"""Email related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure email related settings."""
    # EMAIL
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
    config.EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND")
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
    config.EMAIL_TIMEOUT = 5
    # https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
    config.DEFAULT_FROM_EMAIL = env(
        "DJANGO_DEFAULT_FROM_EMAIL", default="AskAnna Backend <noreply@askanna.io>"
    )
    # https://docs.djangoproject.com/en/dev/ref/settings/#server-email
    config.SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=config.DEFAULT_FROM_EMAIL)
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
    config.EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[AskAnna Backend]")
    config.EMAIL_INVITATION_FROM_EMAIL = env("EMAIL_INVITATION_FROM_EMAIL", default="AskAnna <support@askanna.io>")

    # sendgrid
    # ------------------------------------------------------------------------------
    # https://github.com/sklarsa/django-sendgrid-v5
    # SendGrid Settings
    if config.EMAIL_BACKEND == "sendgrid_backend.SendgridBackend":
        config.EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
        config.SENDGRID_API_KEY = env("SENDGRID_API_KEY")
        config.SENDGRID_SANDBOX_MODE_IN_DEBUG = env.bool("SENDGRID_DEBUG", default=True)

    # https://docs.djangoproject.com/en/dev/ref/settings/#admins
    config.ADMINS = [("""Anna devops""", "devops@askanna.io")]
    # https://docs.djangoproject.com/en/dev/ref/settings/#managers
    config.MANAGERS = config.ADMINS
