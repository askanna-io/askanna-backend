# -*- coding: utf-8 -*-
from django.conf.urls import include
from django.urls import re_path
from job.views import (
    ChunkedArtifactViewSet,
    ChunkedJobResultViewSet,
    JobActionView,
    JobArtifactShortcutView,
    JobArtifactView,
    JobJobRunView,
    JobPayloadView,
    JobRunView,
    JobVariableView,
    ProjectJobViewSet,
    RunMetricsRowView,
    RunMetricsView,
    RunResultCreateView,
    RunResultView,
    RunStatusView,
    RunVariableRowView,
    RunVariablesView,
    StartJobView,
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

runinfo_route.register(
    r"payload",
    JobPayloadView,
    basename="run-payload",
    parents_query_lookups=["jobrun__short_uuid"],
)

artifact_route = runinfo_route.register(
    r"artifact",
    JobArtifactView,
    basename="run-artifact",
    parents_query_lookups=["jobrun__short_uuid"],
)

artifact_route.register(
    r"artifactchunk",
    ChunkedArtifactViewSet,
    basename="artifact-artifactchunk",
    parents_query_lookups=["artifact__jobrun__short_uuid", "artifact__short_uuid"],
)

runresult_route = runinfo_route.register(
    r"result",
    RunResultCreateView,
    basename="run-result",
    parents_query_lookups=["run__short_uuid"],
)

runresult_route.register(
    r"resultchunk",
    ChunkedJobResultViewSet,
    basename="result-resultchunk",
    parents_query_lookups=["runresult__run__short_uuid", "runresult__short_uuid"],
)


urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(r"^(?P<version>(v1))/", include(prouter.urls)),
    re_path(
        r"^(?P<version>(v1))/run/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/?$",
        StartJobView.as_view({"post": "newrun"}, detail=True),
        kwargs={"uuid": None},
        name="run-job",
    ),
    re_path(
        r"^(?P<version>(v1))/result/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/?$",
        RunResultView.as_view({"get": "retrieve"}, detail=True),
        name="shortcut-jobrun-result",
    ),
    re_path(
        r"^(?P<version>(v1))/log/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/?$",
        JobRunView.as_view({"get": "log"}, detail=True),
        kwargs={},
        name="shortcut-jobrun-log",
    ),
    re_path(
        r"^(?P<version>(v1))/status/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/?$",
        RunStatusView.as_view({"get": "retrieve"}, detail=True),
        name="shortcut-jobrun-status",
    ),
    re_path(
        r"^(?P<version>(v1))/artifact/(?P<short_uuid>((?:[a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{4}))/?$",
        JobArtifactShortcutView.as_view({"get": "retrieve"}, detail=True),
        kwargs={},
        name="shortcut-artifact",
    ),
]
