import django.dispatch

avatar_changed_signal = django.dispatch.Signal()
email_changed_signal = django.dispatch.Signal()
password_changed_signal = django.dispatch.Signal()
password_reset_signal = django.dispatch.Signal()
user_created_signal = django.dispatch.Signal()
