AskAnna Backend
===============

AskAnna Backend Project

Local Dev
---------

The required environment variables to run the project are loaded from `.env` files
located in the root directory.
You can manually create a copy of each of the `.env*.example` files or you can run
the following command which will create them for you:

::

  $ docker run -ti --rm -v "${PWD}:/var/lib/dotenver/" jmfederico/dotenver:version-1.2.0 dotenver -r --pattern "**/.env*.example"

You can run this command whenever there are changes to the example config files.
It will never override your custom variables.


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

  # On first run only, to uses locally exposed ports and mounted volumes.
  $ ln -s docker-compose.mutagen.yml docker-compose.override.yml

  # Now launch the containers.
  $ docker-compose up

You can then access askanna_backend via http://localhost:8000/

Remote development
^^^^^^^^^^^^^^^^^^

It is possible to run the project on a remote Docker instance, while developing
locally. Mutagen_ is `integrated with docker-compose`_ to allow you to use external
hardware that can be in your network or in the cloud. File changes are propagated
immediately. This method also improves performance when running Docker in macOS.

Read more on the `docker-compose.mutagen.yml`_ file.

.. _docker-compose.mutagen.yml: ./docker-compose.mutagen.yml
.. _Mutagen: https://mutagen.io
.. _`integrated with docker-compose`: https://mutagen.io/documentation/orchestration/compose


Running additional commands on docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When running in a docker-compose setup, one cannot directly excecute commands on
the containers. E.g. you want to know whether the django service has all the migrations
applied. In a regular dev setup one would issue the following command:


::

  $ python manage.py showmigrations


With docker-compose, one should apply the following command:

::

  $ docker-compose run django python manage.py showmigrations


When you have made changes to the model, one should apply the following command:

::

  $ docker exec -it askanna-backend_django_1 /bin/sh
  $ python manage.py makemigrations

Then, to apply the change your data you need to run the following command:

::

  $ python manage.py migrate


Basic Commands
--------------

Setting Up Your Users
~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html



Celery
~~~~~~

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd askanna_backend
    celery -A config.celery_app worker -l info

Please note: For Celery's import magic to work, it is important *where* the
celery commands are run. If you are in the same folder with *manage.py*, you
should be right.



Sentry
~~~~~~

Sentry is an error logging aggregator service. You can sign up for a free
account at  https://sentry.io/signup/?code=cookiecutter  or download and host
it yourself.
The system is setup with reasonable defaults, including 404 logging and
integration with the WSGI application.

You must set the DSN url in production.
