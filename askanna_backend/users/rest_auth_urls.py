from django.urls import path

from askanna_backend.users.views import PasswordResetStatus, PasswordResetView

urlpatterns = [
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset",),
    path(
        "password/token-status/",
        PasswordResetStatus.as_view({"get": "retrieve"}),
        name="token-status",
    ),
]
