from account.views.me import ProjectMeViewSet
from core.urls import router
from django.conf.urls import include
from django.urls import re_path
from project.views import ProjectView

project_router = router.register(r"project", ProjectView, basename="project")


urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
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
