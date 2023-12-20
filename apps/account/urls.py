from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers

from account.views.account import AccountViewSet
from account.views.me import MeViewSet

router = routers.SimpleRouter()
router.register(
    r"account",
    AccountViewSet,
    basename="account",
)


urlpatterns = [
    re_path(
        r"^(?P<version>(v1))/me/$",
        MeViewSet.as_view(
            actions={
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="me",
    ),
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
