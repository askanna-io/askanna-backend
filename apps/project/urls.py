from django.urls import re_path

from core.urls import router
from project.views.me import ProjectMeViewSet
from project.views.project import ProjectView

project_router = router.register(
    r"project",
    ProjectView,
    basename="project",
)

urlpatterns = [
    re_path(
        r"^(?P<version>(v1))/project/(?P<suuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/?$",
        ProjectMeViewSet.as_view(
            actions={
                "get": "retrieve",
            }
        ),
        name="project-me",
    ),
]
