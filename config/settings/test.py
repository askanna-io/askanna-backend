from .main import *  # noqa: F403

TEST = True

TEST_RESOURCES_DIR = BASE_DIR / "tests" / "resources"  # noqa: F405

# https://docs.djangoproject.com/en/stable/ref/settings/#test-runner
# https://docs.celeryq.dev/projects/django-celery/en/v2.5/cookbook/unit-testing.html
CELERY_ALWAYS_EAGER = True
TEST_RUNNER = "djcelery.contrib.test_runner.CeleryTestSuiteRunner"


INSTALLED_APPS += [  # noqa: F405
    "core.tests.pagination",
]
