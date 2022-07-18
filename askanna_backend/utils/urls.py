import environ
from django.conf import settings
from django.urls import include, path, re_path, reverse_lazy
from django.views.generic import RedirectView
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from utils.views import OpenAPISchemaView

env = environ.Env()
router = DefaultRouter()

urlpatterns = [
    re_path(
        r"^(?P<version>(v1))/",
        include(
            [
                # Redirect to docs by default
                re_path(
                    r"^$",
                    RedirectView.as_view(
                        url=reverse_lazy("schema-swagger-ui", kwargs={"version": "v1"}),
                        permanent=False,
                    ),
                ),
                # Swagger/OpenAPI documentation
                path(
                    "docs/",
                    include(
                        [
                            re_path(
                                r"^swagger(?P<format>\.json|\.yaml)$",
                                OpenAPISchemaView.without_ui(cache_timeout=0),
                                name="schema-json",
                            ),
                            path(
                                r"swagger/",
                                OpenAPISchemaView.with_ui("swagger", cache_timeout=0),
                                name="schema-swagger-ui",
                            ),
                            path(
                                r"redoc/",
                                OpenAPISchemaView.with_ui("redoc", cache_timeout=0),
                                name="schema-redoc",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns.append(path("ht/", include("health_check.urls")))
else:
    healthcheck_token = env.str("HEALTHCHECK_TOKEN", "not-so-secret")
    urlpatterns.append(path(f"ht/{healthcheck_token}/", include("health_check.urls")))
