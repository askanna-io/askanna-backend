"""Settings file for AskAnna backend."""
import sys

import environ

from . import (
    askanna,
    auth,
    celery,
    email,
    files,
    i18n_i10n,
    rest_framework,
    security,
    sentry,
)

ROOT_DIR = environ.Path(__file__) - 3  # (askanna_backend/config/settings/base.py - 3 = askanna_backend/)
APPS_DIR = ROOT_DIR.path("askanna_backend")
RESOURCES_DIR = ROOT_DIR.path("resources")
TESTS_DIR = ROOT_DIR.path("tests")
TEST_RESOURCES_DIR = TESTS_DIR.path("resources")

# Insert the APPS_DIR into PYTHON_PATH to allow easier import from our
# apps housed in /app/askanna_backend
sys.path.insert(0, str(APPS_DIR))

env = environ.Env()

if env.bool("DJANGO_READ_DOT_ENV_FILE", default=False):
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR.path(".env")))

# Setup content paths, finding our askanna modules
sys.path.insert(0, str(APPS_DIR))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

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
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
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
INSTALLED_APPS = [
    # AskAnna apps
    "core",
    "utils",
    "users",
    "workspace",
    "project",
    "package",
    "job",
    "run",
    # Third party apps
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
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.contrib.psutil",  # disk and memory utilization; requires psutil
    "health_check.contrib.redis",
    # Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.TokenAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if env.bool("DJANGO_DEBUG_DB", False):
    print("Turn on dbconnection middleware")
    MIDDLEWARE.append("core.middleware.DebugDBConnectionMiddleware")


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        # https://docs.djangoproject.com/en/stable/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR.path("templates"))],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/stable/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "askanna_backend.utils.context_processors.settings_context",
            ],
        },
    }
]

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(ROOT_DIR.path("fixtures")),)


# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL path.
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")


# Encrypted field settings
FIELD_ENCRYPTION_KEY = env.str("FIELD_ENCRYPTION_KEY", "AguxqQU93Ikh5LWq9NvX9KROx44VMpXqEH0xqpwdFbc=")


# https://docs.djangoproject.com/en/stable/ref/settings/#test-runner
# https://docs.celeryproject.org/projects/django-celery/en/2.4/cookbook/unit-testing.html
TEST_RUNNER = "djcelery.contrib.test_runner.CeleryTestSuiteRunner"


# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/stable/ref/settings/#caches
if env("REDIS_URL", default=None):
    REDIS_URL = env("REDIS_URL")
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimicing memcache behavior.
                # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }

rest_framework.settings(locals(), env)
i18n_i10n.settings(locals(), env)
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
    "DISK_USAGE_MAX": env.float("HEALTHCHECK_DISK_USAGE_MAX", 90),  # percent
    "MEMORY_MIN": env.float("HEALTHCHECK_MEMORY_MIN", 100),  # in MB
}

HEALTHCHECK_CELERY_QUEUE_TIMEOUT = env.float("HEALTHCHECK_CELERY_QUEUE_TIMEOUT", 3)  # seconds
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
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"}
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {
        "level": env.str("DJANGO_ROOT_LOGGING_LEVEL", default="INFO"),
        "handlers": ["console"],
    },
}


if env.bool("DJANGO_DEBUG_TOOLBAR", default=False):
    # django-debug-toolbar
    # ------------------------------------------------------------------------------
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
        "SHOW_TEMPLATE_CONTEXT": True,
    }

TEST = "test" in " ".join(sys.argv)
