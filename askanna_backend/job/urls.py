from django.conf.urls import url, include

from rest_framework import routers

from job.views import *


router = routers.DefaultRouter()
router.register(r'job', JobActionView)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
