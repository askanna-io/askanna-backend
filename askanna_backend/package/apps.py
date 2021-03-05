from django.apps import AppConfig


class PackageConfig(AppConfig):
    name = "package"

    def ready(self):
        from package import signals  # noqa
        from package import listeners  # noqa
