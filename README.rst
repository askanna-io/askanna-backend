AskAnna Backend
===============

AskAnna Backend Project

Settings
--------

Moved to settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Local Dev
---------

For local development, we have two options. One is using Docker and the
configuration based on the `local.yml` file, and another one is by feeding our
own environment variables.

The latter can happen in many different ways, and currently we list two:

- Switching variables via `PyCharm` configurations
- Passing envs via a local .env file and switching on the related variable
  `DJANGO_READ_DOT_ENV_FILE` in the base settings.

We provide a `.env.example` that can be used to set all the required
environment variables in all cases.

Install and running via docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using docker to run locally requires the least effort and when development for 
the askanna-backend is not your primary goal, we advise you to do this setup.

First make sure you have docker installed on your system: 

Consult this guide to install Docker-CE on your Ubuntu sytem: 
https://docs.docker.com/install/linux/docker-ce/ubuntu/ .

Additionally we have a setup which uses docker-compose to launch the whole 
stack of docker images. This requires `docker-compose` to be installed.
Please follow the guide on https://docs.docker.com/compose/install/ to install 
this on your system.

We have setup most of the required variables in the code repository for running 
locally. The next thing is to launch it:

::

  $ docker-compose -f local.yml up

You can then access askanna_backend via http://localhost:8005/


Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the
  form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go
  to your console to see a simulated email verification message. Copy the link
  into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your
superuser logged in on Firefox (or similar), so that you can see how the site
behaves for both kinds of users.

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy askanna_backend

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html



Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd askanna_backend
    celery -A config.celery_app worker -l info

Please note: For Celery's import magic to work, it is important *where* the
celery commands are run. If you are in the same folder with *manage.py*, you
should be right.





Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free
account at  https://sentry.io/signup/?code=cookiecutter  or download and host
it yourself.
The system is setup with reasonable defaults, including 404 logging and
integration with the WSGI application.

You must set the DSN url in production.


Deployment
----------

The following details how to deploy this application.



Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html



