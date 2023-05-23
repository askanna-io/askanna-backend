import urllib

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure askanna related settings."""
    config.ASKANNA_INVITATION_VALID_HOURS = env.int("ASKANNA_INVITATION_VALID_HOURS", 168)
    config.OBJECT_REMOVAL_TTL_HOURS = env.int("OBJECT_REMOVAL_TTL_HOURS", 720)  # default: 30 days

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

    config.ASKANNA_ENVIRONMENT = api_environments.get(parsed_url.netloc.split(".")[0], "review")

    # Setting for deletion of Docker containers after a run
    config.DOCKER_AUTO_REMOVE_TTL_HOURS = env.int("DOCKER_AUTO_REMOVE_TTL_HOURS", default=1)

    # Setting for internal job runs
    config.JOB_CREATE_PROJECT_SUUID = "640q-2AMP-T5BL-Cnml"

    # Setting for avatars
    config.USERPROFILE_DEFAULT_AVATAR = config.RESOURCES_DIR / "assets/src_assets_icons_ask-anna-default-gravatar.png"

    # Set default Docker image for the runner
    config.RUNNER_DEFAULT_DOCKER_IMAGE = env.str("RUNNER_DEFAULT_DOCKER_IMAGE", default="askanna/python:3.11")
    config.RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME = env.str("RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME", default=None)
    config.RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD = env.str("RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD", default=None)
