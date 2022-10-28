from core.urls import router
from django.conf.urls import include, re_path
from job.urls import job_router
from job.views import JobPayloadView
from run.views import (
    ChunkedArtifactViewSet,
    ChunkedJobResultViewSet,
    JobRunView,
    RunArtifactView,
    RunMetricRowView,
    RunMetricView,
    RunResultCreateView,
    RunVariableRowView,
    RunVariableView,
    RunView,
)

run_router = router.register(r"run", RunView)

run_router.register(
    r"metric",
    RunMetricView,
    basename="run-metric",
    parents_query_lookups=["run__short_uuid"],
)

run_router.register(
    r"metric",
    RunMetricRowView,
    basename="run-metric",
    parents_query_lookups=["run_suuid"],
)

run_router.register(
    r"variable",
    RunVariableRowView,
    basename="run-variable",
    parents_query_lookups=["run_suuid"],
)

run_router.register(
    r"variable",
    RunVariableView,
    basename="run-variable",
    parents_query_lookups=["run__short_uuid"],
)

run_router.register(
    r"payload",
    JobPayloadView,
    basename="run-payload",
    parents_query_lookups=["run__short_uuid"],
)

artifact_router = run_router.register(
    r"artifact",
    RunArtifactView,
    basename="run-artifact",
    parents_query_lookups=["run__short_uuid"],
)
artifact_router.register(
    r"artifactchunk",
    ChunkedArtifactViewSet,
    basename="artifact-artifactchunk",
    parents_query_lookups=["artifact__run__short_uuid", "artifact__short_uuid"],
)

result_router = run_router.register(
    r"result-upload",
    RunResultCreateView,
    basename="run-result",
    parents_query_lookups=["run__short_uuid"],
)
result_router.register(
    r"resultchunk",
    ChunkedJobResultViewSet,
    basename="result-resultchunk",
    parents_query_lookups=["runresult__run__short_uuid", "runresult__short_uuid"],
)

job_router.register(
    r"run",
    JobRunView,
    basename="job-run",
    parents_query_lookups=["jobdef__short_uuid"],
)
job_router.register(
    r"metric",
    RunMetricRowView,
    basename="job-run-metric",
    parents_query_lookups=["job_suuid"],
)
job_router.register(
    r"variable_tracked",
    RunVariableRowView,
    basename="job-run-variable",
    parents_query_lookups=["job_suuid"],
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
