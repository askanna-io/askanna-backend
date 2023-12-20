"""Files management related settings."""
from pathlib import Path

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure files related settings."""

    # https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATA_UPLOAD_MAX_MEMORY_SIZE
    # allow 250MB to be used in request.body
    config.DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024  # 250MB

    # FILE_MAX_MEMORY_SIZE is a.o. used to set the maximum memory size for SpooledTemporaryFile and the size of chunks
    config.FILE_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

    # STATIC
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/stable/ref/settings/#static-root
    config.STATIC_ROOT = config.BASE_DIR / "staticfiles"
    # https://docs.djangoproject.com/en/stable/ref/settings/#static-url
    config.STATIC_URL = "/static/"
    # https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#staticfiles-finders
    config.STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    ]

    # FILE STORAGE
    # ------------------------------------------------------------------------------
    if env.str("ASKANNA_STORAGE_ROOT", None):
        config.STORAGE_ROOT = Path(env.str("ASKANNA_STORAGE_ROOT"))
    else:
        config.STORAGE_ROOT = config.BASE_DIR / "storage_root"

    config.RESULT_ROOT = config.STORAGE_ROOT / "artifacts"
    config.METRIC_ROOT = config.STORAGE_ROOT / "artifacts"
    config.VARIABLE_ROOT = config.STORAGE_ROOT / "artifacts"

    config.UPLOAD_DIR_NAME = "upload"
    config.UPLOAD_ROOT = config.STORAGE_ROOT / config.UPLOAD_DIR_NAME

    config.BLOB_DIR_NAME = "blob"
    config.BLOB_ROOT = config.STORAGE_ROOT / config.BLOB_DIR_NAME

    config.PROJECT_DIR_NAME = "projects"
    config.PROJECTS_ROOT = config.STORAGE_ROOT / config.PROJECT_DIR_NAME

    config.PAYLOADS_DIR_NAME = "payloads"
    config.PAYLOADS_ROOT = config.PROJECTS_ROOT / config.PAYLOADS_DIR_NAME

    config.MINIO_SETTINGS = {
        "ENDPOINT": env.str("MINIO_ENDPOINT", default=None),
        "USE_HTTPS": env.bool("MINIO_USE_HTTPS", default=False),
        "EXTERNAL_ENDPOINT": env.str("MINIO_EXTERNAL_ENDPOINT", default=None),
        "EXTERNAL_USE_HTTPS": env.bool("MINIO_EXTERNAL_USE_HTTPS", default=False),
        "ACCESS_KEY": env.str("MINIO_ACCESS_KEY", default=None),
        "SECRET_KEY": env.str("MINIO_SECRET_KEY", default=None),
        "DEFAULT_BUCKET_NAME": env.str("MINIO_DEFAULT_BUCKET_NAME", default="askanna"),
    }

    config.ASKANNA_FILESTORAGE = env.str("ASKANNA_FILESTORAGE", "filesystem")

    config.ASKANNA_DEFAULT_CONTENT_TYPE = "application/octet-stream"

    config.ASKANNA_FILESTORAGE_ALIASES = {
        "filesystem": "storage.filesystem.FileSystemStorage",
        "minio": "storage.minio.MinioStorage",
    }

    config.STORAGES = {
        "default": {
            "BACKEND": config.ASKANNA_FILESTORAGE_ALIASES[config.ASKANNA_FILESTORAGE],
            "OPTIONS": {},
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    # If FileSystemStorage is used, we need to set the storage location of the files and base_url
    if config.ASKANNA_FILESTORAGE == "filesystem":
        config.STORAGES["default"]["OPTIONS"] = {
            "location": str(config.STORAGE_ROOT),
        }
