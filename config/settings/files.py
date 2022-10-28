"""Files management related settings."""

import os

import environ

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
    config.STATIC_ROOT = str(config.ROOT_DIR("staticfiles"))
    # https://docs.djangoproject.com/en/stable/ref/settings/#static-url
    config.STATIC_URL = "/static/"
    # https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#staticfiles-finders
    config.STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    ]
    if env("DJANGO_STATICFILES_STORAGE", default=None):
        config.STATICFILES_STORAGE = env("DJANGO_STATICFILES_STORAGE")

    # MEDIA
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/stable/ref/settings/#media-root
    config.MEDIA_ROOT = str(config.APPS_DIR("media"))
    # https://docs.djangoproject.com/en/stable/ref/settings/#media-url
    config.MEDIA_URL = "/media/"

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
    config.STORAGE_ROOT = config.ROOT_DIR.path("storage_root")

    if env.str("ASKANNA_STORAGE_ROOT", None):
        config.STORAGE_ROOT = environ.Path(env.str("ASKANNA_STORAGE_ROOT"))

    # tmp root is meant for tmp storage for all workers

    config.HOST_TMP_ROOT = str(config.STORAGE_ROOT("tmp"))

    config.TMP_ROOT = str(config.STORAGE_ROOT("tmp"))
    config.ARTIFACTS_ROOT = str(config.STORAGE_ROOT("artifacts"))
    config.PACKAGES_ROOT = str(config.STORAGE_ROOT("packages"))
    config.UPLOAD_ROOT = str(config.STORAGE_ROOT("upload"))
    config.BLOB_ROOT = str(config.STORAGE_ROOT("blob"))
    config.PROJECTS_ROOT = str(config.STORAGE_ROOT("projects"))
    config.PAYLOADS_ROOT = str(config.STORAGE_ROOT.path("projects").path("payloads"))
    config.AVATARS_ROOT = str(config.STORAGE_ROOT("avatars"))

    if env.str("ASKANNA_HOST_TMP_ROOT", None):
        config.HOST_TMP_ROOT = env.str("ASKANNA_HOST_TMP_ROOT")

    # Create the folders if not exists
    for folder in [
        config.ARTIFACTS_ROOT,
        config.AVATARS_ROOT,
        config.PACKAGES_ROOT,
        config.UPLOAD_ROOT,
        config.BLOB_ROOT,
        config.PROJECTS_ROOT,
        config.PAYLOADS_ROOT,
        config.TMP_ROOT,
    ]:
        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)

    # Django large payload receipt
    # https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATA_UPLOAD_MAX_MEMORY_SIZE
    # https://github.com/encode/django-rest-framework/issues/4760#issuecomment-562059446
    # allow 250M to be used in request.body
    config.DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 250
