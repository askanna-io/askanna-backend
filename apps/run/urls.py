from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from run.views import RunArtifactView, RunMetricView, RunVariableView, RunView


class RunMetricRouter(routers.SimpleRouter):
    routes = [
        routers.Route(
            url=r"^{prefix}/{lookup}/metric{trailing_slash}$",
            mapping={
                "get": "metric_list",
                "patch": "metric_update",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={},
        ),
    ]


class RunVariableRouter(routers.SimpleRouter):
    routes = [
        routers.Route(
            url=r"^{prefix}/{lookup}/variable{trailing_slash}$",
            mapping={
                "get": "variable_list",
                "patch": "variable_update",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={},
        ),
    ]


run_router = routers.SimpleRouter()
run_router.register(
    r"run",
    RunView,
    basename="run",
)

run_metric_router = RunMetricRouter()
run_metric_router.register(
    r"run",
    RunMetricView,
    basename="run-metric",
)

run_variable_router = RunVariableRouter()
run_variable_router.register(
    r"run",
    RunVariableView,
    basename="run-variable",
)

artifact_router = routers.SimpleRouter()
artifact_router.register(
    r"run/artifact",
    RunArtifactView,
    basename="run-artifact",
)


urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(artifact_router.urls)),
    re_path(r"^(?P<version>(v1))/", include(run_metric_router.urls)),
    re_path(r"^(?P<version>(v1))/", include(run_variable_router.urls)),
    re_path(r"^(?P<version>(v1))/", include(run_router.urls)),
]
