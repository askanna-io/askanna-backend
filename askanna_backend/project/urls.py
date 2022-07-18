from django.conf.urls import include
from django.urls import re_path
from project.views import ProjectReadOnlyView, ProjectView
from users.views import ProjectMeViewSet
from utils.urls import router
from workspace.urls import workspace_route

project_route = router.register(r"project", ProjectView, basename="project")

workspace_route.register(
    r"projects",
    ProjectReadOnlyView,
    basename="workspace-project",
    parents_query_lookups=["workspace__short_uuid"],
)

urlpatterns = [
    re_path(
        r"^(?P<version>(v1))/project/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/?$",
        ProjectMeViewSet.as_view(),
        kwargs={"object_type": "PR"},
        name="project-me",
    ),
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
