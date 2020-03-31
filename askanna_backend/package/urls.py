from django.conf.urls import url, include
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from package.views import (
    ChunkedPackagePartViewSet,
    PackageViewSet,
    ProjectPackageViewSet,
)
from project.api.views import ProjectListViewShort

router = DefaultRouter()
(
    router
    .register(r"project", ProjectListViewShort, "project")
    .register(r"packages", ProjectPackageViewSet, "project-package", parents_query_lookups=["project__short_uuid"])
)

router.register(r"package", PackageViewSet)
router.register(r"chunkpackagepart", ChunkedPackagePartViewSet)

urlpatterns = [
    url(r"^v1/", include(router.urls)),
]
