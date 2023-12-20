from django.conf.urls import include
from django.urls import re_path
from rest_framework_extensions.routers import ExtendedSimpleRouter

from workspace.views.me import WorkspaceMeViewSet
from workspace.views.people import WorkspacePeopleViewSet
from workspace.views.workspace import WorkspaceViewSet

router = ExtendedSimpleRouter()
workspace_router = router.register(
    r"workspace",
    WorkspaceViewSet,
    basename="workspace",
)
workspace_router.register(
    r"people",
    WorkspacePeopleViewSet,
    basename="workspace-people",
    parents_query_lookups=["workspace__suuid"],
)

urlpatterns = [
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
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
