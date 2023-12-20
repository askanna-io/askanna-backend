from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from package.views import PackageViewSet

router = routers.SimpleRouter()
router.register(
    r"package",
    PackageViewSet,
    basename="package",
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
