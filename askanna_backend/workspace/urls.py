from django.conf.urls import url, include, re_path
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from utils.urls import router
from workspace.views import WorkspaceViewSet

workspace_route = router.register(r"workspace", WorkspaceViewSet)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
