from django.conf.urls import url, include

from rest_framework import routers

from flow.views import FlowActionView


router = routers.DefaultRouter()
router.register(r'flow', FlowActionView)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
