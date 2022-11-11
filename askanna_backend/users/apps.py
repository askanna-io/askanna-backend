from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"
    verbose_name = "Users"

    def ready(self):
        from users import listeners  # noqa
        from users import signals  # noqa
