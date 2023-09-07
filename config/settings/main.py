"""Settings file for AskAnna Backend"""
import sys
from pathlib import Path

import environ

from config.settings import (
    askanna,
    auth,
    celery,
    email,
    files,
    rest_framework,
    security,
    sentry,
)

# BASE_DIR = askanna_backend/config/settings/base.py - 3 = askanna_backend/
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

APPS_DIR = BASE_DIR / "apps"
RESOURCES_DIR = BASE_DIR / "resources"

# Insert the APPS_DIR into PYTHONPATH to allow easier import from our apps housed in the apps directory
sys.path.insert(0, str(APPS_DIR))

env = environ.Env()

if env.bool("DJANGO_READ_DOT_ENV_FILE", default=False):  # type: ignore
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", default=False)  # type: ignore
DEBUG_SQL = env.bool("DJANGO_DEBUG_SQL", default=False)  # type: ignore
TEST = False

# https://docs.djangoproject.com/en/stable/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-TIME_ZONE
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/stable/ref/settings/#use-i18n
USE_I18N = False

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("POSTGRES_DB"),
        "USER": env.str("POSTGRES_USER"),
        "PASSWORD": env.str("POSTGRES_PASSWORD"),
        "HOST": env.str("POSTGRES_HOST"),
        "PORT": env.str("POSTGRES_PORT"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),  # type: ignore
    },
}

# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/stable/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
TOP_OF_THE_LIST_APPS = [
    # http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
    "whitenoise.runserver_nostatic",
]

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
]

THIRD_PARTY_APPS = [
    "django_extensions",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
    # Django rest framework
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "drf_spectacular",
    # Django health check
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.contrib.migrations",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.contrib.psutil",  # disk and memory utilization; requires psutil
    "health_check.contrib.redis",
]

ASKANNA_APPS = [
    "core",
    "storage",
    "account",
    "workspace",
    "project",
    "variable",
    "package",
    "job",
    "run",
]

INSTALLED_APPS = TOP_OF_THE_LIST_APPS + DJANGO_APPS + THIRD_PARTY_APPS + ASKANNA_APPS

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.logging.DebugSqlMiddleware",
]


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        # https://docs.djangoproject.com/en/stable/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/stable/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(BASE_DIR / "fixtures"),)


# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL path.
ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="admin/")  # type: ignore


# Encrypted field settings
FIELD_ENCRYPTION_KEY = env.str("FIELD_ENCRYPTION_KEY", "AguxqQU93Ikh5LWq9NvX9KROx44VMpXqEH0xqpwdFbc=")  # type: ignore


# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#caches
if env.str("REDIS_URL", default=None):  # type: ignore
    REDIS_URL = env.str("REDIS_URL")
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env.str("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimicing memcache behavior.
                # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }

rest_framework.settings(locals(), env)
askanna.settings(locals(), env)
auth.settings(locals(), env)
files.settings(locals(), env)
security.settings(locals(), env)
email.settings(locals(), env)
sentry.settings(locals(), env)
celery.settings(locals(), env)


# HEALTHCHECK
# ------------------------------------------------------------------------------
# https://django-health-check.readthedocs.io/en/stable/settings.html
HEALTH_CHECK = {
    "DISK_USAGE_MAX": env.float("HEALTHCHECK_DISK_USAGE_MAX", 90),  # type: ignore | percentage
    "MEMORY_MIN": env.float("HEALTHCHECK_MEMORY_MIN", 100),  # type: ignore | MB
}

HEALTHCHECK_CELERY_QUEUE_TIMEOUT = env.float("HEALTHCHECK_CELERY_QUEUE_TIMEOUT", 3)  # type: ignore | seconds
HEALTHCHECK_CELERY_RESULT_TIMEOUT = env.float(
    "HEALTHCHECK_CELERY_RESULT_TIMEOUT", HEALTHCHECK_CELERY_QUEUE_TIMEOUT + 1  # seconds
)


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#logging
# See https://docs.djangoproject.com/en/stable/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console_default": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "console_verbose": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "core.middleware.logging": {
            "handlers": ["console_default"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console_verbose"],
        "level": "INFO",
    },
}
