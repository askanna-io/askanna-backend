from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from storage.views import FileViewSet

router = routers.SimpleRouter()
router.register(
    r"storage/file",
    FileViewSet,
    basename="storage-file",
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
