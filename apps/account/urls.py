from django.urls import re_path

from account.views.account import AccountViewSet
from account.views.me import MeViewSet
from core.urls import router

router.register(r"account", AccountViewSet, basename="account")


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
]
