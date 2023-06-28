from django.apps import AppConfig


class PackageConfig(AppConfig):
    name = "package"

    def ready(self):
        from package import listeners, signals  # noqa: F401
