from core.urls import router
from django.conf.urls import include
from django.urls import re_path
from package.views import ChunkedPackagePartViewSet, PackageViewSet

package_router = router.register(
    r"package",
    PackageViewSet,
    basename="package",
)
package_router.register(
    r"packagechunk",
    ChunkedPackagePartViewSet,
    basename="package-packagechunk",
    parents_query_lookups=["package__suuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
