FROM python:3.11-slim-bookworm AS python

ARG BUILD_ENVIRONMENT=local

ENV PYTHONUNBUFFERED=yes
ENV PYTHONDONTWRITEBYTECODE=yes
ENV BUILD_ENV=${BUILD_ENVIRONMENT}


# ---------------------------------------------------------------------------------------------------------------------
# Build Python Wheel archives to speed up future builds
FROM python AS build-wheels

RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
    # Dependency for building Python wheels
    build-essential \
    # Psycopg2 dependency
    libpq-dev

COPY ./requirements .

# Build Python wheels for all requirements for the build environment
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels --requirement ${BUILD_ENVIRONMENT}.txt


# ---------------------------------------------------------------------------------------------------------------------
# Django application image
FROM python AS django

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --assume-yes \
      # Develop dependencies
      sudo bash bash-completion vim git \
      # Psycopg2 dependency
      libpq-dev \
      # Pillow dependencies
      libtiff5-dev libjpeg62-turbo-dev libopenjp2-7-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev \
      tcl8.6-dev tk8.6-dev python3-tk libharfbuzz-dev libfribidi-dev libxcb1-dev \
      # Python-magic depencency
      libmagic-dev \
    # Cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Use wheels from build-stage to install python dependencies
COPY --from=build-wheels /usr/src/app/wheels /wheels/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels/

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

ENTRYPOINT ["/entrypoint"]
