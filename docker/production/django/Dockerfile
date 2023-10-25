ARG BASE_IMAGE=gitlab.askanna.io:4567/askanna/askanna-backend/base:main
FROM $BASE_IMAGE

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=yes
ENV PYTHONDONTWRITEBYTECODE=yes
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install updated requirements over the requirements from the base image
COPY ./requirements /requirements
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --requirement /requirements/${BUILD_ENVIRONMENT}.txt \
    && rm -rf /requirements

COPY --chown=django:django ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./docker/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django ./docker/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY --chown=django:django ./docker/production/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY --chown=django:django ./docker/production/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

COPY --chown=django:django . ${APP_HOME}

RUN chown django:django ${APP_HOME}

ENTRYPOINT ["/entrypoint"]
