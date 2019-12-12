from django.conf.urls import url, include

from rest_framework import routers

from .views import DummyFileViewSet


router = routers.DefaultRouter()
router.register(r'upload', DummyFileViewSet)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
