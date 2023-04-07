# AskAnna Backend

This repository holds code for the AskAnna Backend. Our frontend stack primarily uses
[Django](https://www.djangoproject.com/) and the [Django REST Framework](https://www.django-rest-framework.org/).

## Local Development

You can run the AskAnna Backend locally on your machine. We advise to use Docker Compose to run the AskAnna Backend.
See also the [Run via Docker](#run-via-docker-compose) section.

When you run the AskAnna Backend locally without Docker, make sure you use Python 3.11 or later. The required Python
packages are listed in `requirements/local.txt`. Besides the Python packages, you also need to have a running
PostgreSQL database.

Amongst others to set the PostgreSQL database variables, you can make a copy of each of the `.env.*.example` files
and name it `.env.django` and `.env.postgres` respectively. In these files you can set several environment variables
used by the AskAnna Backend.

### Install Docker Compose

Using Docker Compose to run the AskAnna Backend locally requires the least effort. We advise you to use this setup.

First make sure you have [Docker installed](https://docs.docker.com/engine/install/) on your system. Consult
[this guide](https://docs.docker.com/install/linux/docker-ce/ubuntu/) to install Docker CE on your Ubuntu sytem.

We have a setup which uses Docker Compose to launch the whole stack of Docker images. This requires `docker compose`
to be installed. Please follow [this guide](https://docs.docker.com/compose/install/) to install this on your system.

### Run via Docker Compose

When you run the AskAnna Backend on your local device, you might need to change the linked ports or maybe some other
config. You can add a file `docker-compose.override.yml` to change your local AskAnna Backend configuration. For
example, to change the port you can add the following to the `docker-compose.override.yml` file:

```yaml
version: '3'

services:
  django:
  ports:
    - "8080:8000"
```

If you setup the required environment variables and installed Docker Compose, you are ready to run the AskAnna
Backend. You can launch the AskAnna Backend by running the command:

```shell
docker compose up
```

This will start the environment and show the container logs. With the default settings and when the startup of the
containers finished, you should be able to acces the AskAnna Backend via:
[http://localhost:8000/admin/](http://localhost:8000/admin/)

#### On MacOS

If you run the AskAnna Backend using Docker Compose on MacOS, it could be that you have issues with running jobs.
For Mac we have a workaround to make this work. If you don't have a file `docker-compose.override.yml` you can create
a link to the file `docker-compose.mac.yml` by running:

```shell
ln -s docker-compose.mac.yml docker-compose.override.yml
```

If you have a file `docker-compose.override.yml` you can integrate the content of the file `docker-compose.mac.yml`
into your `docker-compose.override.yml` file.

### Running additional commands on Docker Compose

When running in a Docker Compose setup, one cannot directly excecute commands on the containers. For example, you want
to know whether the Django service has all the migrations applied. In a regular development setup one would issue the
following command:

```python
python manage.py showmigrations
```

With Docker Compose, one should apply the following command:

```shell
docker compose exec django python manage.py showmigrations
```

When you have made changes to the model, one should apply the following commands:

```shell
docker compose exec django python manage.py makemigrations
docker compose exec django python manage.py migrate
```

You can also start a terminal session on the Django container with:

```shell
docker compose exec django /bin/sh
```

### Removing via Docker

In case you don't want to develop or run the AskAnna Backend locally anymore, or something happened which corrupted
your installation, you can execute the following to remove the AskAnna Backend from Docker:

```shell
docker compose rm --stop -v -f
```

This will remove all containers, volumes and networks which where created for the AskAnna Backend to run.

## Basic commands

### Setting up your account

To create a **superuser account**, use this command:

```python
python manage.py createsuperuser
```

**Tip:** to create a normal user account, you can use the REST API. See the API documentation:
[http://localhost:8000/v1/docs/swagger](http://localhost:8000/v1/docs/swagger)

**Docker:** when you run the application via Docker Compose, you need to setup a terminal session to the Docker
container:

```shell
docker compose exec django /bin/sh
```

### Running tests with py.test

```python
pytest
```

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

```shell
pytest --cov=askanna_backend/
coverage html
open htmlcov/index.html
```

### Celery

The AskAnna Backend applications comes with Celery. To run a Celery worker:

```shell
celery -A config.celery_app worker -l info
```

**Please note:** for Celery's import magic to work, it is important *where* the Celery commands are run. If you are in
the same folder with `manage.py`, you should be right.

### Flower

To monitor what's going on in the Celery worker, you can use [Flower](https://flower.readthedocs.io/en/latest/). The
user & password are set in your Django environment file `.env.django` with the variables `CELERY_FLOWER_USER` and
`CELERY_FLOWER_PASSWORD`.

When you develop via Docker, you can open Flower via: [http://localhost:5555](http://localhost:5555)

### Sentry

[Sentry](https://sentry.io/) is an error logging aggregator service. You can [sign up](https://sentry.io/signup/) for
a free account or download and host it yourself. The system is setup with reasonable defaults, including 404 logging
and integration with the WSGI application.

To use Sentry you must set the Sentry DSN url in the environment file `.env.django` with the variable `SENTRY_DSN`.
