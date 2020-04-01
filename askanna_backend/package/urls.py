from django.conf.urls import url, include, re_path
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from package.views import (
    ChunkedPackagePartViewSet,
    PackageViewSet,
    ProjectPackageViewSet,
)
from project.views import ProjectListViewShort

router = DefaultRouter()
(
    router
    .register(r"project", ProjectListViewShort, "project")
    .register(r"packages", ProjectPackageViewSet, "project-package", parents_query_lookups=["project__short_uuid"])
)

router.register(r"package", PackageViewSet)
router.register(r"chunkpackagepart", ChunkedPackagePartViewSet)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
