from django.conf.urls import url, include, re_path
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from workspace.views import MembershipView, UserProfileView
from utils.urls import router
from workspace.views import WorkspaceViewSet

workspace_route = router.register(r"workspace", WorkspaceViewSet)

workspace_route.register(
    r"people",
    MembershipView,
    basename="workspace-people",
    parents_query_lookups=["workspace__short_uuid"],
)
# the userprofile is not created directly but after an invitation is accepted
# workspace_route.register(
#     r"people",
#     UserProfileView,
#     basename="workspace-people",
#     parents_query_lookups=["workspace__short_uuid"],
# )

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
