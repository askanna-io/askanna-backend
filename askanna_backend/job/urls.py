# -*- coding: utf-8 -*-
from django.conf.urls import include
from django.urls import path, re_path

from job.views import (
    ChunkedArtifactViewSet,
    ChunkedJobOutputViewSet,
    JobActionView,
    JobArtifactShortcutView,
    JobArtifactView,
    JobJobRunView,
    JobPayloadView,
    JobResultOutputView,
    JobResultView,
    JobRunView,
    JobVariableView,
    ProjectJobViewSet,
    StartJobView,
    RunMetricsView,
    RunMetricsRowView,
    RunVariablesView,
    RunVariableRowView,
)
from project.urls import project_route
from project.urls import router as prouter
from utils.urls import router

project_route.register(
    r"jobs",
    ProjectJobViewSet,
    basename="project-job",
    parents_query_lookups=["project__short_uuid"],
)

project_route.register(
    r"variables",
    JobVariableView,
    basename="project-variable",
    parents_query_lookups=["project__short_uuid"],
)

job_variable = router.register(r"variable", JobVariableView, basename="variable")
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
job_route.register(
    r"metrics",
    RunMetricsRowView,
    basename="job-metric",
    parents_query_lookups=["job_suuid"],
)
job_route.register(
    r"variables_tracked",
    RunVariableRowView,
    basename="job-variables",
    parents_query_lookups=["job_suuid"],
)


# new url scheme using runinfo

runinfo_route = router.register(r"runinfo", JobRunView, basename="runinfo")

runinfo_route.register(
    r"metrics",
    RunMetricsView,
    basename="run-metric",
    parents_query_lookups=["jobrun__short_uuid"],
)

runinfo_route.register(
    r"metrics",
    RunMetricsRowView,
    basename="run-metric",
    parents_query_lookups=["run_suuid"],
)

runinfo_route.register(
    r"variables",
    RunVariableRowView,
    basename="run-variables",
    parents_query_lookups=["run_suuid"],
)

runinfo_route.register(
    r"variables",
    RunVariablesView,
    basename="run-variables",
    parents_query_lookups=["jobrun__short_uuid"],
)


# older url schemes using jobrun

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
        r"v1/run/<shortuuid:short_uuid>/",
        StartJobView.as_view({"post": "do_ingest_short"}, detail=True),
        kwargs={"uuid": None},
        name="run-job",
    ),
    path(
        r"v1/run/<shortuuid:short_uuid>",
        StartJobView.as_view({"post": "do_ingest_short"}, detail=True),
        kwargs={"uuid": None},
        name="run-job-deprecated",
    ),
    path(
        r"v1/result/<shortuuid:short_uuid>/",
        JobResultView.as_view({"get": "get_result"}, detail=True),
        kwargs={"uuid": None},
        name="shortcut-jobrun-result",
    ),
    path(
        r"v1/result/<shortuuid:short_uuid>",
        JobResultView.as_view({"get": "get_result"}, detail=True),
        kwargs={"uuid": None},
    ),
    path(
        r"v1/log/<shortuuid:short_uuid>/",
        JobRunView.as_view({"get": "log"}, detail=True),
        kwargs={},
        name="shortcut-jobrun-log",
    ),
    path(
        r"v1/log/<shortuuid:short_uuid>",
        JobRunView.as_view({"get": "log"}, detail=True),
        kwargs={},
    ),
    path(
        r"v1/status/<shortuuid:short_uuid>/",
        JobResultView.as_view({"get": "get_status"}, detail=True),
        kwargs={"uuid": None},
        name="shortcut-jobrun-status",
    ),
    path(
        r"v1/status/<shortuuid:short_uuid>",
        JobResultView.as_view({"get": "get_status"}, detail=True),
        kwargs={"uuid": None},
    ),
    path(
        r"v1/artifact/<shortuuid:short_uuid>/",
        JobArtifactShortcutView.as_view({"get": "retrieve"}, detail=True),
        kwargs={},
        name="shortcut-artifact",
    ),
    path(
        r"v1/artifact/<shortuuid:short_uuid>",
        JobArtifactShortcutView.as_view({"get": "retrieve"}, detail=True),
        kwargs={},
    ),
]
