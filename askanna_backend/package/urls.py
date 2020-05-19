from django.conf.urls import url, include, re_path
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from package.views import (
    ChunkedPackagePartViewSet,
    PackageViewSet,
    ProjectPackageViewSet,
)
from project.views import ProjectListViewShort
from project.urls import project_route, router as prouter

router = DefaultRouter()

router.register(r"package", PackageViewSet)

project_route.register(r"packages", ProjectPackageViewSet, "project-package", parents_query_lookups=["project__short_uuid"])
project_route.register(r"packagechunk", ChunkedPackagePartViewSet, "project-packagechunk", parents_query_lookups=["project__short_uuid"])

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
    re_path(r"^(?P<version>(v1|v2))/", include(prouter.urls)),
]
