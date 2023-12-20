from urllib.parse import urlparse

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure AskAnna related settings"""
    config.ASKANNA_INVITATION_VALID_HOURS = env.int("ASKANNA_INVITATION_VALID_HOURS", 168)
    config.OBJECT_REMOVAL_TTL_HOURS = env.int("OBJECT_REMOVAL_TTL_HOURS", 720)  # default: 30 days
    config.ALLOWED_API_AGENTS = (
        "API",
        "CLI",
        "PYTHON-SDK",
        "WEBUI",
        "WORKER",
    )

    config.ASKANNA_API_URL = env.str("ASKANNA_API_URL")
    config.ASKANNA_UI_URL = env.str("ASKANNA_UI_URL", "")

    # Determine whether we are beta/production/review, defaults to 'review'
    api_environments = {
        "api": "production",
        "beta-api": "beta",
    }
    parsed_url = urlparse(config.ASKANNA_API_URL)
    config.ASKANNA_ENVIRONMENT = api_environments.get(parsed_url.netloc.split(".")[0], "review")

    # Set default Docker image for the runner
    config.RUNNER_DEFAULT_DOCKER_IMAGE = env.str("RUNNER_DEFAULT_DOCKER_IMAGE", default="askanna/python:3.11")
    config.RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME = env.str("RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME", default=None)
    config.RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD = env.str("RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD", default=None)

    # Setting for deletion of Docker containers after a run
    config.DOCKER_AUTO_REMOVE_TTL_HOURS = env.int("DOCKER_AUTO_REMOVE_TTL_HOURS", default=1)
