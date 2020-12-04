import django

password_reset_signal = django.dispatch.Signal(providing_args=["users", "request", "domain", "email"])
