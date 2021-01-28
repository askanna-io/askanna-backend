from django.conf.urls import include, re_path
from users.views import PersonViewSet
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
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
