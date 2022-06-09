"""Django Rest Framework related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, _env):
    """Configure Django Rest Framework related settings."""
    config.REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "core.auth.PassthroughAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
        "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
        "DEFAULT_FILTER_BACKENDS": [
            "rest_framework.filters.OrderingFilter",
            "django_filters.rest_framework.DjangoFilterBackend",
        ],
    }
