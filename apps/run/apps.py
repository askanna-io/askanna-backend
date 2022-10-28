from django.apps import AppConfig


class RunConfig(AppConfig):
    name = "run"

    def ready(self):
        from run import listeners, signals  # noqa: F401
