from django.conf.urls import include, re_path

from utils.urls import router
from project.views import ProjectView, ProjectReadOnlyView
from workspace.urls import workspace_route

project_route = router.register(r"project", ProjectView, basename="project")

workspace_route.register(
    r"projects",
    ProjectReadOnlyView,
    basename="workspace-project",
    parents_query_lookups=["workspace__short_uuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
