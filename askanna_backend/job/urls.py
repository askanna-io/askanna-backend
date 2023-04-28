from django.conf.urls import include
from django.urls import re_path

from core.urls import router
from job.views import JobView

job_router = router.register(r"job", JobView, basename="job")

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
