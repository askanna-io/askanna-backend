from django.conf.urls import include, re_path
from package.views import (
    ChunkedPackagePartViewSet,
    PackageViewSet,
    ProjectPackageViewSet,
)
from project.urls import project_route
from project.urls import router as prouter
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

router = DefaultRouter()

package_router = router.register(r"package", PackageViewSet)

project_route.register(
    r"packages",
    ProjectPackageViewSet,
    "project-package",
    parents_query_lookups=["project__short_uuid"],
)

package_router.register(
    r"packagechunk",
    ChunkedPackagePartViewSet,
    "package-packagechunk",
    parents_query_lookups=["package__short_uuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(r"^(?P<version>(v1))/", include(prouter.urls)),
]
