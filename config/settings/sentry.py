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
    # Sentry (https://docs.sentry.io/platforms/python/)
    # ------------------------------------------------------------------------------
    if env("SENTRY_DSN", default=None):
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )
        sentry_sdk.init(
            dsn=env.str("SENTRY_DSN"),
            traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", 0.05),
            server_name=config.ASKANNA_API_URL,
            integrations=[
                sentry_logging,
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            # Associate users to errors
            # https://docs.sentry.io/platforms/python/configuration/options/#send-default-pii
            send_default_pii=True,
        )
