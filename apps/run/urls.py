from django.urls import include, re_path

from core.urls import router
from job.views import JobPayloadView
from run.views import (
    ChunkedArtifactViewSet,
    ChunkedJobResultViewSet,
    RunArtifactView,
    RunMetricUpdateView,
    RunMetricView,
    RunResultCreateView,
    RunVariableUpdateView,
    RunVariableView,
    RunView,
)

run_router = router.register(r"run", RunView)

run_router.register(
    r"metric",
    RunMetricView,
    basename="run-metric",
    parents_query_lookups=["run__suuid"],
)

run_router.register(
    r"metric",
    RunMetricUpdateView,
    basename="run-metric",
    parents_query_lookups=["run__suuid"],
)

run_router.register(
    r"variable",
    RunVariableView,
    basename="run-variable",
    parents_query_lookups=["run__suuid"],
)

run_router.register(
    r"variable",
    RunVariableUpdateView,
    basename="run-variable",
    parents_query_lookups=["run__suuid"],
)

run_router.register(
    r"payload",
    JobPayloadView,
    basename="run-payload",
    parents_query_lookups=["run__suuid"],
)

artifact_router = run_router.register(
    r"artifact",
    RunArtifactView,
    basename="run-artifact",
    parents_query_lookups=["run__suuid"],
)
artifact_router.register(
    r"artifactchunk",
    ChunkedArtifactViewSet,
    basename="artifact-artifactchunk",
    parents_query_lookups=["artifact__run__suuid", "artifact__suuid"],
)

result_router = run_router.register(
    r"result-upload",
    RunResultCreateView,
    basename="run-result",
    parents_query_lookups=["run__suuid"],
)
result_router.register(
    r"resultchunk",
    ChunkedJobResultViewSet,
    basename="result-resultchunk",
    parents_query_lookups=["runresult__run__suuid", "runresult__suuid"],
)


urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
