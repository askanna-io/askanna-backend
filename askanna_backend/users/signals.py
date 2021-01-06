import django

password_reset_signal = django.dispatch.Signal(
    providing_args=["users", "request", "domain", "email"]
)
user_created_signal = django.dispatch.Signal(
    providing_args=["user", "request", "workspace_name"]
)

password_changed_signal = django.dispatch.Signal(providing_args=["user", "request"])

email_changed_signal = django.dispatch.Signal(
    providing_args=["user", "request", "old_email"]
)
