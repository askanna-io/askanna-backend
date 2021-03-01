from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views
from django.views.generic.base import RedirectView


urlpatterns = [
    path("", RedirectView.as_view(url=settings.ASKANNA_UI_URL), name="home"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Authentication support over django drf
    path("rest-auth/", include("users.rest_auth_urls")),
    path("rest-auth/", include("rest_auth.urls")),
    # API Urls
    path("", include("utils.urls")),
    path("", include("project.urls")),
    path("", include("job.urls")),
    # path("", include("flow.urls")),
    path("", include("package.urls")),
    path("", include("workspace.urls")),
    path("", include("project_template.urls")),
    path("", include("users.urls")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    print("Adding urls for DEBUG")
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
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
    ] + static("/files/", document_root=str(settings.ROOT_DIR("storage_root")))
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
