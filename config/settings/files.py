"""Files management related settings."""
from pathlib import Path

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure files related settings."""
    # WhiteNoise
    # ------------------------------------------------------------------------------
    # http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
    config.INSTALLED_APPS = [
        "whitenoise.runserver_nostatic",
    ] + config.INSTALLED_APPS

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
    if env("DJANGO_STATICFILES_STORAGE", default=None):
        config.STATICFILES_STORAGE = env("DJANGO_STATICFILES_STORAGE")

    # FILE STORAGE
    # ------------------------------------------------------------------------------
    # AskAnna implementation, we use the file storage to store:
    # - packages
    # - ...
    # Location of this file storage is NOT within the container as we need to have this
    # accessible by many other containers to serve or maintain/compute on
    # For clarity reasons, we put this in the code root under `storage_root`
    # In which in production will mount to the host location or anything else
    # FIXME: replace this with a distributed file storage such as `minio` or `S3`

    if env.str("ASKANNA_STORAGE_ROOT", None):
        config.STORAGE_ROOT = Path(env.str("ASKANNA_STORAGE_ROOT"))
    else:
        config.STORAGE_ROOT = config.BASE_DIR / "storage_root"

    config.ARTIFACTS_DIR_NAME = "artifacts"
    config.ARTIFACTS_ROOT = config.STORAGE_ROOT / config.ARTIFACTS_DIR_NAME

    config.PACKAGES_DIR_NAME = "packages"
    config.PACKAGES_ROOT = config.STORAGE_ROOT / config.PACKAGES_DIR_NAME

    config.UPLOAD_DIR_NAME = "upload"
    config.UPLOAD_ROOT = config.STORAGE_ROOT / config.UPLOAD_DIR_NAME

    config.BLOB_DIR_NAME = "blob"
    config.BLOB_ROOT = config.STORAGE_ROOT / config.BLOB_DIR_NAME

    config.PROJECT_DIR_NAME = "projects"
    config.PROJECTS_ROOT = config.STORAGE_ROOT / config.PROJECT_DIR_NAME

    config.PAYLOADS_DIR_NAME = "payloads"
    config.PAYLOADS_ROOT = config.PROJECTS_ROOT / config.PAYLOADS_DIR_NAME

    config.AVATARS_DIR_NAME = "avatars"
    config.AVATARS_ROOT = config.STORAGE_ROOT / config.AVATARS_DIR_NAME

    # Django large payload receipt
    # https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATA_UPLOAD_MAX_MEMORY_SIZE
    # https://github.com/encode/django-rest-framework/issues/4760#issuecomment-562059446
    # allow 250M to be used in request.body
    config.DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 250
