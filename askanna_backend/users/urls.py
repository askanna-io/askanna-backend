from django.conf.urls import include, re_path

from utils.urls import router
from users.views import UserView

user_route = router.register(r"accounts", UserView)

urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
