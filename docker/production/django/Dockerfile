ARG BASE_IMAGE=gitlab.askanna.io:4567/askanna/askanna-backend/base:main
FROM $BASE_IMAGE

ENV PYTHONUNBUFFERED 1

COPY ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint
RUN chown django /entrypoint

COPY ./docker/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start
RUN chown django /start

COPY ./docker/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker
RUN chown django /start-celeryworker

COPY ./docker/production/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat
RUN chown django /start-celerybeat

COPY ./docker/production/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

COPY . /app

# Install updated requirements over the requirements from base-image
COPY ./requirements /requirements
RUN pip install -U pip && pip install --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

RUN chown -R django /app

# USER django

EXPOSE 5000

WORKDIR /app

ENTRYPOINT ["/entrypoint"]