from django.conf.urls import include, re_path

from utils.urls import router
from users.views import UserView, BaseMeViewSet, MeAvatarViewSet

user_route = router.register(r"accounts", UserView)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
    re_path(r"^(?P<version>(v1|v2))/me/$", BaseMeViewSet.as_view(), name="global-me"),
    re_path(
        r"^(?P<version>(v1|v2))/me/avatar/$",
        MeAvatarViewSet.as_view(),
        name="global-me-avatar",
    ),
]
