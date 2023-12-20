from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from project.views.me import ProjectMeViewSet
from project.views.project import ProjectView

router = routers.SimpleRouter()
router.register(
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
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
