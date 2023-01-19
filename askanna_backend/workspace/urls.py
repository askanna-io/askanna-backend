from core.urls import router
from django.conf.urls import include
from django.urls import re_path
from users.views.me import WorkspaceMeAvatarViewSet, WorkspaceMeViewSet
from users.views.people import PeopleViewSet
from workspace.views import WorkspaceViewSet

workspace_router = router.register(
    r"workspace",
    WorkspaceViewSet,
    basename="workspace",
)
workspace_people_router = workspace_router.register(
    r"people",
    PeopleViewSet,
    basename="workspace-people",
    parents_query_lookups=["workspace__suuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(
        r"^(?P<version>(v1))/workspace/(?P<suuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/?$",
        WorkspaceMeViewSet.as_view(
            actions={
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="workspace-me",
    ),
    re_path(
        r"^(?P<version>(v1))/workspace/(?P<suuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/avatar/?$",
        WorkspaceMeAvatarViewSet.as_view(
            actions={
                "put": "update",
                "delete": "destroy",
            }
        ),
        name="workspace-me-avatar",
    ),
]
