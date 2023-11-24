from django.apps import AppConfig
from health_check.plugins import plugin_dir


class StorageConfig(AppConfig):
    name = "storage"

    def ready(self):
        from health_check.storage.backends import DefaultFileStorageHealthCheck

        from storage import listeners, signals  # noqa: F401

        plugin_dir.register(DefaultFileStorageHealthCheck)
