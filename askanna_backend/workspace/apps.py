from django.apps import AppConfig


class WorkspaceConfig(AppConfig):
    name = "workspace"

    def ready(self):
        from workspace import listeners  # noqa: F401
