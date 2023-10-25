from django.apps import AppConfig


class ProjectConfig(AppConfig):
    name = "project"

    def ready(self):
        from project import listeners  # noqa: F401
