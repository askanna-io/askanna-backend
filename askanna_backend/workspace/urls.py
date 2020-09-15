from django.conf.urls import url, include, re_path
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from workspace.views import MembershipView
from utils.urls import router
from workspace.views import WorkspaceViewSet

from rest_framework.routers import Route, SimpleRouter


class CustomRouter(SimpleRouter):
    routes = [
        Route(
            url=r'workspace/{parent_lookup_workspace__short_uuid}',
            mapping={'get': 'list'},
            name='membership-list',
            detail=False,
            initkwargs={'suffix': 'List'}

        ),
        Route(
            url=r'workspace/{parent_lookup_workspace__short_uuid}/people/{short_uuid}',
            mapping={'get': 'retrieve'},
            name='userprofile-detail',
            detail=True,
            initkwargs={'suffix': 'Detail'}
        ),
    ]


workspace_route = router.register(r"workspace", WorkspaceViewSet)

routerr = CustomRouter()
routerr.register(
    r"people",
    MembershipView,
    basename="workspace-people",
    # parents_query_lookups=["workspace__short_uuid"],
)
urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
    re_path(r"^(?P<version>(v1|v2))/", include(routerr.urls)),
]
