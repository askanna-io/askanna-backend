from django.conf.urls import url, include, re_path

from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from utils.urls import router
from project.views import ProjectListViewShort


project_route = router.register(
    r"project",
    ProjectListViewShort,
    basename="project"
)

urlpatterns = [
    re_path(r'^(?P<version>(v1|v2))/', include(router.urls)),
]
