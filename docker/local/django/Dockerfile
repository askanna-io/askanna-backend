FROM python:3.11-alpine AS base

ARG BUILD_ENVIRONMENT=local

ENV PYTHONUNBUFFERED 1

RUN apk update \
    # psycopg2 dependencies
    && apk add --virtual build-deps gcc python3-dev musl-dev openssl-dev cargo \
    && apk add libpq-dev \
    # Pillow dependencies
    && apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
    # CFFI dependencies
    && apk add libffi-dev py-cffi \
    # https://docs.djangoproject.com/en/stable/ref/django-admin/#dbshell
    && apk add postgresql-client \
    && apk add git \
    && apk add libmagic

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install -U pip \
    pip install -r /requirements/${BUILD_ENVIRONMENT}.txt

COPY ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./docker/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./docker/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./docker/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./docker/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

RUN mkdir /app
WORKDIR /app

ENTRYPOINT ["/entrypoint"]


# Flower image to expose port 5555
FROM base AS flower

EXPOSE 5555


# Django image to expose port 5555
FROM base AS django

EXPOSE 8000

# Default image with no exposed ports
FROM base AS default
