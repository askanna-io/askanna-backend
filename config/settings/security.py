"""Security related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure security related settings."""
    # https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
    config.SECRET_KEY = env("DJANGO_SECRET_KEY")
    # https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
    config.ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

    # SECURITY
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
    config.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
    config.SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    # https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
    config.SESSION_COOKIE_SECURE = True
    # https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
    config.CSRF_COOKIE_SECURE = True
    # https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
    config.SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60)
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
    config.SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(config.SECURE_HSTS_SECONDS)
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
    config.SECURE_HSTS_PRELOAD = bool(config.SECURE_HSTS_SECONDS)

    if env.bool("DJANGO_ENABLE_CORS_HANDLING", default=False):
        config.INSTALLED_APPS = [
            "corsheaders",
        ] + config.INSTALLED_APPS
        config.CORS_ALLOW_ALL_ORIGINS = True

        config.MIDDLEWARE = [
            "corsheaders.middleware.CorsMiddleware",
        ] + config.MIDDLEWARE

    if config.DEBUG:
        # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
        config.INTERNAL_IPS = env.list("DJANGO_INTERNAL_IPS", default=["127.0.0.1"])
        if env("USE_DOCKER") == "yes":
            import socket

            hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
            config.INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]
