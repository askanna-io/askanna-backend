"""
WSGI config for the AskAnna Backend project.

This module contains the WSGI application used by Django's development server and any production WSGI deployments. It
exposes the WSGI callable as a module-level variable named `application`. Django's `runserver` and `runfcgi` commands
discover this application via the `WSGI_APPLICATION` setting.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.main")

application = get_wsgi_application()
