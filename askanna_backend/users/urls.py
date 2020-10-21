from django.urls import path, re_path, include
from utils.urls import router
from users.views import UserView

from askanna_backend.users.views import (
    user_redirect_view,
    user_update_view,
    user_detail_view,
)

user_route = router.register(r"accounts", UserView)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),

]




