from django.conf.urls import include, re_path
from users.views import BaseMeViewSet, MeAvatarViewSet, UserView
from utils.urls import router

user_route = router.register(r"accounts", UserView)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
    re_path(r"^(?P<version>(v1))/me/$", BaseMeViewSet.as_view(), name="global-me"),
    re_path(
        r"^(?P<version>(v1))/me/avatar/$",
        MeAvatarViewSet.as_view(),
        name="global-me-avatar",
    ),
]
