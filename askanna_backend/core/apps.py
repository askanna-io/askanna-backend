from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from core import signals  # noqa
        from core import utils  # noqa
