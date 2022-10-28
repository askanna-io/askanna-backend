from core.urls import router
from django.conf.urls import include
from django.urls import re_path
from job.views import JobActionView, JobPayloadView, ProjectJobViewSet, StartJobView
from project.urls import project_router

job_router = router.register(r"job", JobActionView, basename="job")

job_router.register(
    r"payload",
    JobPayloadView,
    basename="job-payload",
    parents_query_lookups=["jobdef__short_uuid"],
)

project_router.register(
    r"job",
    ProjectJobViewSet,
    basename="project-job",
    parents_query_lookups=["project__short_uuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(
        r"^(?P<version>(v1))/job/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/run/request/batch/?$",
        StartJobView.as_view({"post": "newrun"}, detail=True),
        name="run-job",
    ),
]
