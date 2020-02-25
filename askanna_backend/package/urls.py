from django.conf.urls import url, include

from rest_framework import routers

from package.views import PackageViewSet, ChunkedPackagePartViewSet


router = routers.DefaultRouter()
router.register(r'package', PackageViewSet)
router.register(r'chunkpackagepart', ChunkedPackagePartViewSet)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
