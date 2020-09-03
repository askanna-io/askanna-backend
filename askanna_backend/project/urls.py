from django.conf.urls import url, include, re_path

from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from utils.urls import router
from project.views import ProjectView
from workspace.urls import workspace_route, router as wrouter

project_route = router.register(r"project", ProjectView, basename="project")

workspace_route.register(
    r"projects",
    ProjectView,
    basename="workspace-project",
    parents_query_lookups=["workspace__short_uuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
