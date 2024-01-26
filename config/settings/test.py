from .main import *  # noqa: F403

TEST_RESOURCES_DIR = BASE_DIR / "tests/resources"  # noqa: F405

INSTALLED_APPS += [  # noqa: F405
    "core.tests.pagination",
]


# Celery test settings
# -------------------------------------------------------------------------------------
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = True

# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True
