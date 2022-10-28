from core.urls import router
from django.conf.urls import include
from django.urls import re_path
from users.views import ObjectAvatarMeViewSet, ObjectMeViewSet, PersonViewSet
from workspace.views import WorkspaceViewSet

workspace_router = router.register(r"workspace", WorkspaceViewSet)
workspace_people_router = workspace_router.register(
    r"people",
    PersonViewSet,
    basename="workspace-people",
    parents_query_lookups=["workspace__short_uuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(
        r"^(?P<version>(v1))/workspace/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/avatar/?$",
        ObjectAvatarMeViewSet.as_view(),
        kwargs={"object_type": "WS"},
        name="workspace-me-avatar",
    ),
    re_path(
        r"^(?P<version>(v1))/workspace/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/me/?$",
        ObjectMeViewSet.as_view(),
        kwargs={"object_type": "WS"},
        name="workspace-me",
    ),
]
