import environ
from django.conf import settings
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.versioning import URLPathVersioning
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

env = environ.Env()
router = DefaultRouter()

urlpatterns = [
    re_path(
        r"^(?P<version>(v1))/docs/schema/",
        SpectacularAPIView.as_view(versioning_class=URLPathVersioning),
        name="api-schema",
    ),
    re_path(
        r"^(?P<version>(v1))/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-swagger",
    ),
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns.append(path("ht/", include("health_check.urls")))
else:
    healthcheck_token = env.str("HEALTHCHECK_TOKEN", "not-so-secret")
    urlpatterns.append(path(f"ht/{healthcheck_token}/", include("health_check.urls")))
