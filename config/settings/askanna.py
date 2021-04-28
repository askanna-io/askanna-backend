"""Askanna related settings."""

import urllib

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure askanna related settings."""
    config.ASKANNA_INVITATION_VALID_HOURS = env.int(
        "ASKANNA_INVITATION_VALID_HOURS", 168
    )

    api_environments = {
        "api": "production",
        "beta-api": "beta",
    }

    default_ui_url = {
        "api": "https://askanna.eu",
        "beta-api": "https://beta.askanna.eu",
    }

    config.ASKANNA_API_URL = env.str("ASKANNA_API_URL", "https://api.askanna.io")
    config.ASKANNA_CDN_URL = env.str("ASKANNA_CDN_URL", "https://cdn-api.askanna.io")

    # Determine whether we are beta/production/review, defaults to 'review'
    parsed_url = urllib.parse.urlparse(config.ASKANNA_API_URL)

    config.ASKANNA_UI_URL = env.str(
        "ASKANNA_UI_URL",
        default_ui_url.get(parsed_url.netloc.split(".")[0], "https://beta.askanna.eu"),
    )

    config.ASKANNA_ENVIRONMENT = api_environments.get(
        parsed_url.netloc.split(".")[0], "review"
    )

    # AskAnna Docker settings
    config.ASKANNA_DOCKER_USER = env.str("ASKANNA_DOCKER_USER", default=None)
    config.ASKANNA_DOCKER_PASS = env.str("ASKANNA_DOCKER_PASS", default=None)

    # Setting for deletion of Docker containers after a run
    config.DOCKER_AUTO_REMOVE_CONTAINER = env.bool(
        "DOCKER_AUTO_REMOVE_CONTAINER", default=False
    )
    config.DOCKER_AUTO_REMOVE_TTL = env.int(
        "DOCKER_AUTO_REMOVE_TTL", default=1
    )

    # Setting for internal job runs
    config.JOB_CREATE_PROJECT_SUUID = "640q-2AMP-T5BL-Cnml"

    # Setting for avatars
    config.USERPROFILE_DEFAULT_AVATAR = (
        "assets/src_assets_icons_ask-anna-default-gravatar.png"
    )

    # Set default docker image for the runner
    config.RUNNER_DEFAULT_DOCKER_IMAGE = (
        "gitlab.askanna.io:4567/askanna/askanna-cli:3.7-slim-master"
    )
