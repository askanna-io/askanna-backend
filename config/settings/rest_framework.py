"""Django Rest Framework related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, _env):
    """Configure Django Rest Framework related settings."""
    config.REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.TokenAuthentication",
        ],
        "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
        "DEFAULT_PAGINATION_CLASS": "askanna_backend.core.pagination.CursorPagination",
        "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
        "DEFAULT_FILTER_BACKENDS": [
            "askanna_backend.core.filters.OrderingFilter",
            "rest_framework.filters.SearchFilter",
            "django_filters.rest_framework.DjangoFilterBackend",
        ],
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    }

    config.SPECTACULAR_SETTINGS = {
        "TITLE": "AskAnna API",
        "DESCRIPTION": "The AskAnna API can be used to interact with the AskAnna Backend.",
        "TOS": "https://askanna.io/terms/",
        "CONTACT": {
            "name": "AskAnna Support",
            "email": "support@askanna.io",
        },
        "LICENSE": {
            "name": "GNU Affero General Public License",
            "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
        },
        "EXTERNAL_DOCS": {
            "url": "https://docs.askanna.io",
            "description": "AskAnna Documentation",
        },
        "VERSION": None,
        "SCHEMA_PATH_PREFIX": "/v[0-9]",
        "SERVE_INCLUDE_SCHEMA": False,
        "SWAGGER_UI_SETTINGS": {
            # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
            "deepLinking": True,
            "defaultModelsExpandDepth": -1,
            "defaultModelExpandDepth": 3,
            "displayRequestDuration": True,
            "docExpansion": "none",
        },
    }
