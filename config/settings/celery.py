"""Celery related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure Celery related settings."""
    # Celery
    # ------------------------------------------------------------------------------
    if config.USE_TZ:
        # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-timezone
        config.CELERY_TIMEZONE = config.TIME_ZONE

    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url
    config.CELERY_BROKER_URL = env("CELERY_BROKER_URL")
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_backend
    # http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#django-celery-results-using-the-django-orm-cache-as-a-result-backend
    config.CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="django-db")
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
    config.CELERY_ACCEPT_CONTENT = ["json"]
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_serializer
    config.CELERY_TASK_SERIALIZER = "json"
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_serializer
    config.CELERY_RESULT_SERIALIZER = "json"
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-time-limit
    # TODO: set to whatever value is adequate in your circumstances

    # Disabled the limit
    # config.CELERY_TASK_TIME_LIMIT = 241 * 60 # 241 minutes, replace worker
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-soft-time-limit
    # TODO: set to whatever value is adequate in your circumstances
    # config.CELERY_TASK_SOFT_TIME_LIMIT = 240 * 60 # max length of 1 job to log

    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#beat-scheduler
    config.CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

    config.CELERY_WORKER_MAX_TASKS_PER_CHILD = 1

    if config.DEBUG:
        # http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-propagates
        config.CELERY_TASK_EAGER_PROPAGATES = True
