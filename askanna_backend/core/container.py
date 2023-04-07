import datetime
import logging
import time
from collections.abc import Callable

import docker
import redis
from django.conf import settings
from django.db import IntegrityError
from job.models import RunImage

TEMPLATES_PATH = str(settings.APPS_DIR.path("templates"))


class RegistryAuthenticationError(Exception):
    ...


class RegistryContainerPullError(Exception):
    ...


def get_descriptive_docker_error(docker_error) -> str:
    """
    Translate cryptic errors from docker sdk to AskAnna friendly messages
    """

    # manifest for {repo-image} not found: manifest unknown: manifest unknown
    # Get https://registry-1.docker.io/v2/: unauthorized: incorrect username or password
    if "not found" in docker_error:
        return "The image was not found, please check your askanna.yml whether the environment image is correct."
    if "unauthorized" in docker_error or "access forbidden" in docker_error:
        return "We could not authenticate you to the registry. Please check the environment username and password."
    return docker_error


class RegistryImageHelper:
    def __init__(
        self,
        client: docker.DockerClient,
        image_path: str,
        username: str | None = None,
        password: str | None = None,
        logger: Callable[[str], None] = lambda x: None,
        *args,
        **kwargs,
    ):
        self.image_path = image_path
        self.image_repository, self.image_tag = docker.utils.parse_repository_tag(self.image_path)  # type: ignore
        if not self.image_tag:
            self.image_tag = ""
        self.image_registry, self.image_repo_name = docker.auth.resolve_repository_name(  # type: ignore
            self.image_repository
        )

        self.username = username
        self.password = password

        self.client = client

        self.logger = logger

        self.userinfo = None
        if self.credentials:
            self.login()
        self.image_info = None

    def login(self):
        """
        Authenticate to the registry
        """
        auth_config = {"registry": self.image_registry, "reauth": True}
        if self.credentials and not self.userinfo:
            auth_config.update(**self.credentials)
            try:
                loginresponse = self.client.login(**auth_config)
            except docker.errors.APIError as exc:  # type: ignore
                message = f"Credentials are not correct to log in onto {self.image_registry}"
                logging.info(message)
                logging.info(get_descriptive_docker_error(exc.explanation))
                self.logger(message)
                raise RegistryAuthenticationError(message) from exc
            except Exception as exc:
                message = f"Could not authenticate onto: {self.image_registry}"
                logging.info(message)
                logging.info(exc)
                self.logger(message)
                raise RegistryAuthenticationError(message) from exc
            else:
                self.userinfo = loginresponse

    @property
    def credentials(self) -> dict:
        if self.username and self.password:
            return {"username": self.username, "password": self.password}
        return {}

    def get_image_info(self) -> docker.models.images.RegistryData:  # type: ignore
        """
        Get information about the image, may require authentication
        We will always authenticate first before getting information if username and password is set
        """
        if not self.image_info:
            self.login()

            try:
                self.image_info = self.client.images.get_registry_data(self.image_path, auth_config=self.credentials)
            except docker.errors.APIError as exc:  # type: ignore
                message = f"Could not pull image: {self.image_path}"
                logging.info(message)
                logging.info(get_descriptive_docker_error(exc.explanation))
                self.logger(message)
                self.logger(get_descriptive_docker_error(exc.explanation))
                raise RegistryContainerPullError(message) from exc

        return self.image_info

    @property
    def image_digest(self) -> str:
        return self.get_image_info().id

    @property
    def image_short_id(self) -> str:
        return self.get_image_info().short_id.replace("sha256:", "")

    def pull(self, log=False):
        self.login()

        pull_spec = {
            "repository": self.image_path,
            "stream": True,
            "decode": True,
        }
        if self.credentials:
            pull_spec.update(**{"auth_config": self.credentials})

        try:
            logging.info(f"Pulling image: {self.image_path}")
            image = self.client.api.pull(**pull_spec)
        except (docker.errors.NotFound, docker.errors.APIError) as exc:  # type: ignore
            message = f"Could not pull image: {self.image_path}"
            logging.info(message)
            logging.info(get_descriptive_docker_error(exc.explanation))
            self.logger(message)
            self.logger(get_descriptive_docker_error(exc.explanation))
            raise RegistryContainerPullError(message) from exc
        except Exception as exc:
            message = f"Could not pull image: {self.image_path}"
            logging.info(message)
            logging.info(exc)
            self.logger(message)
            raise RegistryContainerPullError(message) from exc
        else:
            if log:
                map(lambda line: self.logger(line.get("status")), image)


class ContainerImageBuilder:
    def __init__(
        self,
        client: docker.DockerClient,
        image_helper: RegistryImageHelper,
        image_prefix: str = settings.ASKANNA_ENVIRONMENT,
        image_dockerfile_path: str = TEMPLATES_PATH,
        image_dockerfile: str = "Dockerfile",
        logger: Callable[[str], None] = lambda x: None,
    ) -> None:
        self.image_helper = image_helper
        self.image_prefix = image_prefix
        self.image_dockerfile_path = image_dockerfile_path
        self.image_dockerfile = image_dockerfile
        self.client = client
        self.logger = logger
        self.redis = redis.Redis.from_url(settings.REDIS_URL)

    def get_build_lock(self, run_image):
        return self.redis.get(run_image.suuid)

    def set_build_lock(self, run_image):
        self.redis.set(run_image.suuid, datetime.datetime.utcnow().isoformat())
        return self.get_build_lock(run_image)

    def remove_build_lock(self, run_image):
        return self.redis.delete(run_image.suuid)

    def wait_for_build_lock(self, run_image: RunImage, timeout: int = 300):
        timeout_stamp = time.time() + timeout
        while self.get_build_lock(run_image) is not None:
            time.sleep(1)
            if time.time() > timeout_stamp:
                message = f"Timeout while waiting for image '{run_image.name}' to be built by another run."
                logging.warning(message)
                self.logger(message)
                self.logger(
                    "The image is currently being built by another run. We waited for 5 minutes, but it did not "
                    "finish. You can try again later or contact support if this problem persists."
                )
                raise TimeoutError(message)

    def get_image_object(self, name: str, tag: str, digest: str) -> tuple[RunImage, bool]:
        try:
            run_image, created = RunImage.objects.get_or_create(name=name, tag=tag, digest=digest)
        except RunImage.MultipleObjectsReturned:
            run_image = RunImage.objects.filter(name=name, tag=tag, digest=digest).order_by("-created_at").first()
            created = False
            logging.warning(
                "Multiple objects returned for RunImage, using the most recent one. More info:\n"
                f"  name: {name}\n"
                f"  tag: {tag}\n"
                f"  digest: {digest}"
            )
        except IntegrityError:
            # If the image was created in another run, we could get an IntegrityError. In that case, we try to get the
            # image from the database.
            run_image = RunImage.objects.get(name=name, tag=tag, digest=digest)
            created = False

        if not run_image:
            # This should never happen, but just in case a final check if we have a run_image
            raise RunImage.DoesNotExist

        return run_image, created

    def image_exist(self, image: str) -> bool:
        """Check if an image is available locally."""
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:  # type: ignore
            return False
        else:
            return True

    def get_image(self) -> RunImage:
        """Get an image from the registry or build it if it does not exist locally."""
        run_image, created = self.get_image_object(
            name=self.image_helper.image_repository,
            tag=self.image_helper.image_tag,
            digest=self.image_helper.image_digest,
        )

        if not created and not run_image.cached_image and self.get_build_lock(run_image) is not None:
            # The image was created in another run, wait for it during 5 minutes. Else, raise an error.
            self.wait_for_build_lock(run_image)
            run_image.refresh_from_db()

        if run_image.cached_image and not self.image_exist(run_image.cached_image):
            logging.info(f"Cached image {run_image.cached_image} not found. A trigger to rebuild the image is set.")
            run_image.unset_cached_image()

        if created or not run_image.cached_image:
            logging.info(f"Building image {self.image_helper.image_path}")
            run_image = self.build_image(run_image=run_image)

        return run_image

    def build_image(self, run_image: RunImage):
        self.set_build_lock(run_image)

        from_image = f"{self.image_helper.image_repository}@{self.image_helper.image_digest}"

        repository_name = f"aa-{self.image_prefix}-{run_image.suuid}".lower()
        repository_tag = self.image_helper.image_short_id
        askanna_repository_image = f"{repository_name}:{repository_tag}"

        try:
            image, _ = self.client.images.build(  # type: ignore
                path=self.image_dockerfile_path,
                dockerfile=self.image_dockerfile,
                pull=True,
                tag=askanna_repository_image,
                rm=True,
                forcerm=True,
                buildargs={"IMAGE": from_image},
            )
        except docker.errors.DockerException as exc:  # type: ignore
            self.logger(f"Preparing the run image with image '{self.image_helper.image_repository}' failed:")
            self.logger(exc.msg)
            self.logger("Please follow the instructions on https://docs.askanna.io/ to build your own image.")
            raise exc
        else:
            run_image.set_cached_image(askanna_repository_image)
            logging.info(f"Image {askanna_repository_image} built and cached. Image digest: {image.short_id}")
        finally:
            self.remove_build_lock(run_image)

        return run_image
