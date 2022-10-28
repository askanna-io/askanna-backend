import datetime
import time
import typing

import docker
import redis

from config.settings.main import env


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
    elif "unauthorized" in docker_error or "access forbidden" in docker_error:
        return "We could not authenticate you to the registry. Please check the environment username and password."
    return docker_error


class RegistryImageHelper:
    def __init__(
        self,
        client: docker.DockerClient,
        image_uri: str,
        username: str = None,
        password: str = None,
        logger: typing.Callable[[str], None] = lambda x: x,
        *args,
        **kwargs,
    ):
        self.client = client
        self.image_uri = image_uri
        self.repository, self.image_tag = docker.utils.parse_repository_tag(image_uri)
        self.registry, self.repo_name = docker.auth.resolve_repository_name(self.repository)
        self.username = username
        self.password = password
        self.logger = logger
        self.userinfo = None
        self.imageinfo = None

    def login(self):
        """
        Authenticate to the registry
        """
        auth_config = {"registry": self.registry, "reauth": True}
        if self.username and not self.userinfo:
            auth_config.update(**self.credentials)
            try:
                loginresponse = self.client.login(**auth_config)
            except docker.errors.APIError as e:
                self.logger(f"Could not pull image: {self.image_uri}")
                self.logger(f"Credentials are not correct to login onto {self.registry}")
                print(e.explanation)
                raise RegistryAuthenticationError(f"Credentials are not correct to login onto {self.registry}")
            except Exception as e:
                print("-" * 30)
                print(e)
                print("-" * 30)

                self.logger(f"Could not pull image: {self.image_uri}")
                raise RegistryAuthenticationError(f"Could not authenticate onto {self.registry}")
            else:
                # store the loginresponse for later useage
                self.userinfo = loginresponse

    @property
    def credentials(self) -> dict:
        if self.username and self.password:
            return {"username": self.username, "password": self.password}
        return {}

    def info(self) -> docker.models.images.RegistryData:
        """
        Get information about the image, may require authentication
        We will always authenticate first before getting information if username and password is set
        """
        if self.credentials and not self.userinfo:
            self.login()

        if not self.imageinfo:
            try:
                self.imageinfo = self.client.images.get_registry_data(self.image_uri, auth_config=self.credentials)
            except docker.errors.APIError as e:
                self.logger(f"Could not pull image: {self.image_uri}")
                self.logger(get_descriptive_docker_error(e.explanation))
                print(e.explanation)
                raise RegistryContainerPullError(f"Could not pull image: {self.image_uri}")
        return self.imageinfo

    @property
    def id(self) -> str:
        return self.info().attrs.get("Id")

    @property
    def image_sha(self) -> str:
        return self.info().attrs.get("Descriptor", {}).get("digest")

    @property
    def short_id(self) -> str:
        """
        Unique identifier for the containerimage
        """
        return self.info().short_id

    @property
    def short_id_nosha(self) -> str:
        """
        Unique identifier for the containerimage
        """
        return self.short_id.replace("sha256:", "")

    def pull(self, log=False):
        """
        Pull the image
        """
        # just call the `.info()` once to setup auth
        self.info()
        pull_spec = {
            "repository": self.image_uri,
            "stream": True,
            "decode": True,
        }
        if self.credentials:
            pull_spec.update(**{"auth_config": self.credentials})

        try:
            print("Try pulling", self.image_uri)
            image = self.client.api.pull(**pull_spec)
        except (docker.errors.NotFound, docker.errors.APIError) as e:
            self.logger(f"Could not pull image: {self.image_uri}")
            self.logger(get_descriptive_docker_error(e.explanation))
            print(e.explanation)
            raise RegistryContainerPullError(f"Image not found: {self.image_uri}")
        except Exception as e:
            print("-" * 30)
            print(e)
            print("-" * 30)
            self.logger(f"Could not pull image: {self.image_uri}")
            raise RegistryContainerPullError(f"Could not pull image: {self.image_uri}")
        else:
            if log:
                map(lambda line: self.logger(line.get("status")), image)


class ContainerImageBuilder:
    def __init__(
        self,
        client: docker.DockerClient,
        logger: typing.Callable[[str], None] = lambda x: x,
    ) -> None:
        self.client = client
        self.logger = logger
        self.redis_url = env("REDIS_URL")
        self.redis = redis.Redis.from_url(self.redis_url)

    def get_build_lock(self, run_image):
        return self.redis.get(run_image.short_uuid)

    def set_build_lock(self, run_image):
        self.redis.set(run_image.short_uuid, datetime.datetime.utcnow().isoformat())
        return self.get_build_lock(run_image)

    def remove_build_lock(self, run_image):
        return self.redis.delete(run_image.short_uuid)

    def get_image(
        self,
        repository,
        tag,
        digest,
        imagehelper,
        model=None,
        docker_debug_log=False,
        image_prefix="review",
        image_template_path="templates/",
    ):
        if not model:
            raise RuntimeError("No model specified to lookup the RunImage")

        # rule:
        # Can we find the image_short_id in db?
        #   yes: set runner_image to prebuild_image name
        #   no: pull and build
        run_image, _created = model.objects.get_or_create(
            **{
                "name": repository,
                "tag": tag,
                "digest": digest,
            }
        )

        if not _created and not run_image.cached_image:
            # the image was created in another run, wait for it
            while self.get_build_lock(run_image) is not None:
                time.sleep(5.0)
            # retrieve newest information from the database
            run_image.refresh_from_db()

        if _created or not run_image.cached_image:
            self.set_build_lock(run_image)
            # this is a new image
            # pull image first
            # might raise `RegistryContainerPullError`
            imagehelper.pull(log=docker_debug_log)

            # build the new image
            # tag into askanna repo
            repository_name = f"{image_prefix}-aa-{run_image.short_uuid}".lower()
            repository_tag = imagehelper.short_id_nosha
            askanna_repository_image_version_name = f"{repository_name}:{repository_tag}"

            try:
                image, buildlog = self.build(
                    from_image=f"{imagehelper.repository}@{imagehelper.image_sha}",
                    tag=askanna_repository_image_version_name,
                    template_path=image_template_path,
                    dockerfile="custom_Dockerfile",
                )
            except docker.errors.DockerException as e:
                self.logger(f"Run could not be started because of run errors in the image {imagehelper.repository}")
                self.logger(e.msg)
                self.logger("Please follow the instructions on https://docs.askanna.io/ to build your own image.")
                raise e

            run_image.cached_image = askanna_repository_image_version_name
            run_image.save(update_fields=["cached_image"])
            # we just created the image with the following short_id:
            print(image.short_id)
            self.remove_build_lock(run_image)

            if docker_debug_log:
                # log the build steps into the log, only in DEBUG mode
                map(lambda x: self.logger(x.get("stream")), buildlog)
        return run_image

    def build(
        self,
        from_image=None,
        tag=None,
        template_path=None,
        dockerfile=None,
    ) -> None:

        image, buildlog = self.client.images.build(
            **{
                "path": template_path,
                "dockerfile": dockerfile,
                "pull": True,
                "tag": tag,
                "rm": True,
                # Always remove intermediate containers, even after unsuccessful builds
                "forcerm": True,
                "buildargs": {
                    "IMAGE": from_image,
                },
            }
        )
        return image, buildlog
