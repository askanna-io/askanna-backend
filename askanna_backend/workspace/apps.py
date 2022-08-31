from django.apps import AppConfig


class WorkspaceConfig(AppConfig):
    name = "workspace"
    verbose_name = "workspaces"

    def ready(self):
        from workspace import listeners  # noqa
