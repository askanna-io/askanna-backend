from core.urls import router
from django.conf.urls import include
from django.urls import re_path
from project.views import ProjectReadOnlyView, ProjectVariableView, ProjectView
from users.views import ProjectMeViewSet
from workspace.urls import workspace_router

project_router = router.register(r"project", ProjectView, basename="project")

project_router.register(
    r"variable",
    ProjectVariableView,
    basename="project-variable",
    parents_query_lookups=["project__suuid"],
)

variable_router = router.register(r"variable", ProjectVariableView, basename="variable")

workspace_router.register(
    r"project",
    ProjectReadOnlyView,
    basename="workspace-project",
    parents_query_lookups=["workspace__suuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(
        r"^(?P<version>(v1))/project/(?P<suuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/?$",
        ProjectMeViewSet.as_view(),
        kwargs={"object_type": "PR"},
        name="project-me",
    ),
]
