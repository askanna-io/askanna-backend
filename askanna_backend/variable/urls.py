from django.conf.urls import include
from django.urls import re_path

from core.urls import router
from variable.views import VariableView

variable_router = router.register(r"variable", VariableView, basename="variable")


urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
