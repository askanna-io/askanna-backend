from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from job.views import JobView

router = routers.SimpleRouter()
router.register(
    r"job",
    JobView,
    basename="job",
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
