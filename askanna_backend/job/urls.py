from django.conf.urls import url, include, re_path
from django.urls import path, re_path, register_converter

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from job.views import (
    JobActionView,
    StartJobView,
    ProjectJobViewSet,
    JobRunView,
    JobJobRunView,
)
from project.urls import project_route, router as prouter
from utils.urls import router

project_route.register(
    r"jobs",
    ProjectJobViewSet,
    basename="project-job",
    parents_query_lookups=["project__short_uuid"],
)

job_route = router.register(r"job", JobActionView, basename="job")
# job_route.register(
#     r"runs",
#     JobJobRunView,
#     basename="job-runs",
#     parents_query_lookups=["jobdef__short_uuid"],
# )

jobrun_route = router.register(r"jobrun", JobRunView, basename="jobrun")

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
    re_path(r"^(?P<version>(v1|v2))/", include(prouter.urls)),
    re_path(
        r"^(?P<version>(v1|v2))/run/<shortuuid:short_uuid>$",
        StartJobView.as_view({"post": "do_ingest_short"}),
        kwargs={"uuid": None},
    ),
    re_path(
        r"^(?P<version>(v1|v2))/run/<uuid:uuid>$",
        StartJobView.as_view({"post": "do_ingest"}),
    ),
]
