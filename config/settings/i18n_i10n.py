"""Localization and internationalization related settings."""
from django.utils.translation import gettext_lazy as _

from .settings_decorator import configclass


@configclass
def settings(config, _env):
    """Configure localization and internationalization related settings."""
    # Local time zone. Choices are
    # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    # though not all of them may be available with every OS.
    # In Windows, this must be set to your system time zone.
    config.TIME_ZONE = "UTC"
    # https://docs.djangoproject.com/en/dev/ref/settings/#language-code
    config.LANGUAGE_CODE = "en-us"
    # https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
    config.USE_I18N = True
    # https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
    config.USE_L10N = True
    # https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
    config.USE_TZ = True
    # https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
    config.LOCALE_PATHS = [config.ROOT_DIR.path("locale")]
    # https://docs.djangoproject.com/en/3.1/ref/settings/#languages
    config.LANGUAGES = [
        ("en", _("English")),
    ]
