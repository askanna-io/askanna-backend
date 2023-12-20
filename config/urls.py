from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path, reverse_lazy
from django.views import defaults as default_views
from django.views.generic.base import RedirectView

urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Authentication support over Django DRF
    re_path(r"^(?P<version>(v1))/auth/", include("account.rest_auth_urls")),
    # API Urls
    path("", include("core.urls")),
    path("", include("storage.urls")),
    path("", include("account.urls")),
    path("", include("workspace.urls")),
    path("", include("project.urls")),
    path("", include("variable.urls")),
    path("", include("package.urls")),
    path("", include("job.urls")),
    path("", include("run.urls")),
    path(
        "",
        RedirectView.as_view(
            url=reverse_lazy("api-swagger", kwargs={"version": "v1"}),
            permanent=False,
        ),
        name="home",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit these url in browser to see how these
    # error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
