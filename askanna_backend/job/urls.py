from django.conf.urls import url, include, re_path
from django.urls import path, re_path, register_converter

from job.views import (
    JobActionView,
    StartJobView,
    ProjectJobViewSet,
    JobResultView,
    JobRunView,
    JobJobRunView,
    JobArtifactView,
    JobPayloadView,
    JobResultView,
    ChunkedArtifactViewSet,
    ChunkedJobOutputViewSet,
    JobResultOutputView,
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
job_route.register(
    r"runs",
    JobJobRunView,
    basename="job-runs",
    parents_query_lookups=["jobdef__short_uuid"],
)
job_route.register(
    r"payload",
    JobPayloadView,
    basename="job-payload",
    parents_query_lookups=["jobdef__short_uuid"],
)

jobrun_route = router.register(r"jobrun", JobRunView, basename="jobrun")
jobrun_route.register(
    r"payload",
    JobPayloadView,
    basename="jobrun-payload",
    parents_query_lookups=["jobrun__short_uuid"],
)
artifact_route = jobrun_route.register(
    r"artifact",
    JobArtifactView,
    basename="jobrun-artifact",
    parents_query_lookups=["jobrun__short_uuid"],
)

artifact_route.register(
    r"artifactchunk",
    ChunkedArtifactViewSet,
    basename="artifact-artifactchunk",
    parents_query_lookups=["artifact__jobrun__short_uuid", "artifact__short_uuid"],
)

jobresult_route = jobrun_route.register(
    r"result",
    JobResultOutputView,
    basename="jobrun-result",
    parents_query_lookups=["jobrun__short_uuid"],
)

jobresult_route.register(
    r"resultchunk",
    ChunkedJobOutputViewSet,
    basename="result-resultchunk",
    parents_query_lookups=["joboutput__jobrun__short_uuid", "joboutput__short_uuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
    re_path(r"^(?P<version>(v1|v2))/", include(prouter.urls)),
    path(
        r"v1/run/<shortuuid:short_uuid>",
        StartJobView.as_view({"post": "do_ingest_short"}),
        kwargs={"uuid": None},
    ),
    path(r"v1/run/<uuid:uuid>", StartJobView.as_view({"post": "do_ingest"}),),

    path(
        r"v1/result/<shortuuid:short_uuid>",
        JobResultView.as_view({"get": "get_result"}),
        kwargs={"uuid": None},
    ),

    path(
        r"v1/log/<shortuuid:short_uuid>",
        JobRunView.as_view({"get": "log"}),
        kwargs={},
    ),

    path(
        r"v1/status/<shortuuid:short_uuid>",
        JobResultView.as_view({"get": "get_status"}),
        kwargs={"uuid": None},
    ),

    path(
        r"v1/artifact/<shortuuid:short_uuid>",
        JobArtifactView.as_view({"get": "retrieve"}),
        kwargs={},
    ),
]
