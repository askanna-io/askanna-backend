# AskAnna Backend

The AskAnna Backend application build in Django.

## Local Development

The required environment variables to run the project are loaded from `.env` files located in the root directory. You
can manually create a copy of each of the `.env*.example` files or you can run the following command which will create
them for you:

```bash
docker run -ti --rm -v "${PWD}:/var/lib/dotenver/" jmfederico/dotenver:version-1.2.0 dotenver -r --pattern "**/.env*.example"
```

You can run this command whenever there are changes to the example config files. It will never override your custom
variables.

### Install Docker

Using Docker to run locally requires the least effort and when development for the `askanna-backend` is not your primary
goal, we advise you to do this setup.

First make sure you have Docker installed on your system:
[https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

Consult this guide to install Docker CE on your Ubuntu sytem:
[https://docs.docker.com/install/linux/docker-ce/ubuntu/](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

Additionally we have a setup which uses Docker Compose to launch the whole stack of Docker images. This requires
`docker-compose` to be installed. Please follow the guide to install this on your system:
[https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

### Run via Docker

When you run the AskAnna Backend the first time on your local device, you need to locally expose ports and mount
volumes. You can do this with the command:

```bash
ln -s docker-compose.local.yml docker-compose.override.yml
```

If you setup the required environment variables and installed Docker, we are ready to run the AskAnna Backend. You can
launch the AskAnna Backend by running the command:

```bash
docker-compose up
```

You can then access the AskAnna Backend via: [http://localhost:8000/admin/](http://localhost:8000/admin/)

#### On MacOS

If you run the AskAnna Backend using Docker Compose on MacOS, it could be that you have issues with running jobs.
In the file [docker-compose.yml](docker-compose.yml), you can replace line 15 with the next line and it should work.

```yaml
      - /var/run/docker.sock.raw:/var/run/docker.sock:ro
```

### Running additional commands on Docker

When running in a Docker Compose setup, one cannot directly excecute commands on the containers. E.g. you want to know
whether the Django service has all the migrations applied. In a regular development setup one would issue the following
command:

```python
python manage.py showmigrations
```

With Docker Compose, one should apply the following command:

```bash
docker-compose run django python manage.py showmigrations
```

When you have made changes to the model, one should apply the following command:

```bash
docker exec -it askanna-backend_django_1 /bin/sh
python manage.py makemigrations
python manage.py migrate
```

### Removing docker-compose setup

In case you don't want to develop or run `askanna-backend` locally anymore, or something happened which corrupted your
installation. You can execute the following to remove `askanna-backend` from your system:

```bash
docker-compose rm --stop -v -f
```

This will remove all volumes which where created for `askanna-backend` to run.

## Basic commands

### Setting up your account

To create a **superuser account**, use this command:

```python
python manage.py createsuperuser
```

When you logged in as super user, you can also create a normal user via the Django admin:
[http://localhost:8000/admin/account/user/add/](http://localhost:8000/admin/account/user/add/)

**Tip:** for convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox
(or similar), so that you can see how the site behaves for both kinds of accounts.

**Hint:** when you run the application via Docker Compose, you need to setup a terminal session to the Docker
container:

```bash
docker exec -it askanna-backend_django_1 /bin/sh
```

### Type checks

Running type checks with mypy:

```python
mypy askanna_backend
```

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

```bash
pytest --cov=askanna_backend/
coverage html
open htmlcov/index.html
```

### Running tests with py.test

```python
pytest
```

### Celery

The AskAnna Backend applications comes with Celery. To run a Celery worker:

```bash
cd askanna_backend
celery -A config.celery_app worker -l info
```

Please note: for Celery's import magic to work, it is important *where* the Celery commands are run. If you are in the
same folder with `manage.py`, you should be right.

### Flower

To monitor what's going on in the Celery worker, you can use [Flower](https://flower.readthedocs.io/en/latest/). The
user & password are set in your Django environment file `.env.django` with the variables `CELERY_FLOWER_USER` and
`CELERY_FLOWER_PASSWORD`.

When you develop locally, you can open Flower via: [http://localhost:5555](http://localhost:5555)

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at
[https://sentry.io/signup/](https://sentry.io/signup/) or download and host it yourself. The system is setup with
reasonable defaults, including 404 logging and integration with the WSGI application.

To use Sentry you must set the Sentry DSN url in the environment file for Django.
