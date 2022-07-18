# -*- coding: utf-8 -*-
from django.conf.urls import include
from django.urls import re_path
from users.views import ObjectAvatarMeViewSet, ObjectMeViewSet, PersonViewSet
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
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
