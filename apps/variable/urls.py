from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from variable.views import VariableView

router = routers.SimpleRouter()
router.register(
    r"variable",
    VariableView,
    basename="variable",
)


urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
