"""Sentry related settings."""

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure Sentry related settings."""
    # Sentry
    # ------------------------------------------------------------------------------
    if env("SENTRY_DSN", default=None):
        config.SENTRY_DSN = env("SENTRY_DSN")
        config.SENTRY_LOG_LEVEL = env.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)

        sentry_logging = LoggingIntegration(
            level=config.SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )
        sentry_sdk.init(
            dsn=config.SENTRY_DSN,
            traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", 0.1),
            server_name=config.ASKANNA_API_URL,
            integrations=[
                sentry_logging,
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            # Associate users to errors
            # https://docs.sentry.io/platforms/python/configuration/options/#send-default-pii
            send_default_pii=True
        )
