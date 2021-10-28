# -*- coding: utf-8 -*-
from django.conf.urls import include
from django.urls import path, re_path
from users.views import PersonViewSet, ObjectMeViewSet, ObjectAvatarMeViewSet
from utils.urls import router
from workspace.views import WorkspaceViewSet

workspace_route = router.register(r"workspace", WorkspaceViewSet)
workspace_people_route = workspace_route.register(
    r"people",
    PersonViewSet,
    basename="workspace-people",
    parents_query_lookups=["workspace__short_uuid"],
)

urlpatterns = [
    path(
        r"v1/workspace/<shortuuid:short_uuid>/me/avatar/",
        ObjectAvatarMeViewSet.as_view(),
        kwargs={"object_type": "WS"},
        name="workspace-me-avatar",
    ),
    path(
        r"v1/workspace/<shortuuid:short_uuid>/me/",
        ObjectMeViewSet.as_view(),
        kwargs={"object_type": "WS"},
        name="workspace-me",
    ),
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
