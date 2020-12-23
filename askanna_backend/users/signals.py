import django

password_reset_signal = django.dispatch.Signal(
    providing_args=["users", "request", "domain", "email"]
)
user_created_signal = django.dispatch.Signal(
    providing_args=["user", "request", "workspace_name"]
)

