"""Askanna related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure askanna related settings."""
    config.ASKANNA_INVITATION_VALID_HOURS = env.int("ASKANNA_INVITATION_VALID_HOURS", 168)

    config.ASKANNA_API_URL = env.str("ASKANNA_API_URL", "https://api.askanna.io")
    config.ASKANNA_CDN_URL = env.str("ASKANNA_CDN_URL", "https://cdn-api.askanna.io")
    config.ASKANNA_UI_URL = env.str("ASKANNA_UI_URL", "https://askanna.io")

    # AskAnna Docker settings
    config.ASKANNA_DOCKER_USER = env.str("ASKANNA_DOCKER_USER", default=None)
    config.ASKANNA_DOCKER_PASS = env.str("ASKANNA_DOCKER_PASS", default=None)

    # Setting for deletion of Docker containers after a run
    config.DOCKER_AUTO_REMOVE_CONTAINER = env.bool("DOCKER_AUTO_REMOVE_CONTAINER", default=False)
