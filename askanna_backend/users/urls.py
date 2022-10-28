from core.urls import router
from django.conf.urls import include, re_path
from users.views import BaseMeViewSet, MeAvatarViewSet, UserView

user_router = router.register(r"account", UserView)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(r"^(?P<version>(v1))/me/$", BaseMeViewSet.as_view(), name="global-me"),
    re_path(
        r"^(?P<version>(v1))/me/avatar/$",
        MeAvatarViewSet.as_view(),
        name="global-me-avatar",
    ),
]
