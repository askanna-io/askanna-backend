from core.urls import router
from package.views import PackageViewSet

router.register(
    r"package",
    PackageViewSet,
    basename="package",
)

urlpatterns = []
