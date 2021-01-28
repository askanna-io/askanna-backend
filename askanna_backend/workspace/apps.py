from django.apps import AppConfig


class WorkspaceConfig(AppConfig):
    name = "workspace"
    verbose_name = "workspaces"

    def ready(self):
        from workspace import signals  # noqa
        from workspace import listeners  # noqa
