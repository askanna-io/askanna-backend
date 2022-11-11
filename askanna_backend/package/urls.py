from core.urls import router
from django.conf.urls import include, re_path
from package.views import (
    ChunkedPackagePartViewSet,
    PackageViewSet,
    ProjectPackageViewSet,
)
from project.urls import project_router

package_router = router.register(r"package", PackageViewSet)

project_router.register(
    r"package",
    ProjectPackageViewSet,
    "project-package",
    parents_query_lookups=["project__suuid"],
)

package_router.register(
    r"packagechunk",
    ChunkedPackagePartViewSet,
    "package-packagechunk",
    parents_query_lookups=["package__suuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
