from account.views.user import (
    PasswordResetTokenStatusView,
    PasswordResetView,
    UserDetailsView,
)
from dj_rest_auth.views import LoginView, LogoutView, PasswordResetConfirmView
from django.urls import path

urlpatterns = [
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    path(
        "password/reset/token-status/",
        PasswordResetTokenStatusView.as_view(actions={"get": "retrieve"}),
        name="rest_password_reset_token_status",
    ),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    # URLs from dj_rest_auth, but need to import them here to prevent overwriting the user URL. By default the
    # dj_rest_auth.user URL has a PUT and PATCH methods which we don't need here.
    path("login/", LoginView.as_view(), name="rest_login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="rest_password_reset_confirm"),
]
