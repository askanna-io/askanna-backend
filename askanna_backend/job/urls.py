from django.conf.urls import url, include
from django.urls import path

from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from job.views import JobActionView, StartJobView


router = routers.DefaultRouter()
router.register(r'job', JobActionView)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
    path(r'v1/run/<uuid:uuid>', StartJobView.as_view({'post': 'do_ingest'}))
]
