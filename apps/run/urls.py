from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers
from rest_framework_extensions.routers import ExtendedSimpleRouter

from run.views.artifact import RunArtifactView
from run.views.metric import RunMetricUpdateView, RunMetricView
from run.views.run import RunView
from run.views.variable import RunVariableUpdateView, RunVariableView

router = ExtendedSimpleRouter()

run_router = router.register(
    r"run",
    RunView,
    basename="run",
)

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


artifact_router = routers.SimpleRouter()
artifact_router.register(
    r"run/artifact",
    RunArtifactView,
    basename="run-artifact",
)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(artifact_router.urls)),
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
