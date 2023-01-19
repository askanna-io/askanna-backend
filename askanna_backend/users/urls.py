from core.urls import router
from django.conf.urls import include, re_path
from users.views.account import AccountViewSet
from users.views.me import MeAvatarViewSet, MeViewSet

account_router = router.register(r"account", AccountViewSet, basename="account")

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(
        r"^(?P<version>(v1))/me/$",
        MeViewSet.as_view(
            actions={
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="askanna-me",
    ),
    re_path(
        r"^(?P<version>(v1))/me/avatar/$",
        MeAvatarViewSet.as_view(
            {
                "put": "update",
                "delete": "destroy",
            }
        ),
        name="askanna-me-avatar",
    ),
]
