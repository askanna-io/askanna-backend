from django.conf.urls import url, include, re_path

from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from project.api.views import ProjectListViewShort


router = DefaultRouter()
project_route = router.register(
    r"project",
    ProjectListViewShort,
    basename="project"
)

urlpatterns = [
    re_path(r'^(?P<version>(v1|v2))/', include(router.urls)),
]
