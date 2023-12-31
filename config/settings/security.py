"""Security related settings."""
import ipaddress
import logging

from .settings_decorator import configclass

logger = logging.getLogger(__name__)


class IpNetworks:
    """
    A Class that contains a list of IPvXNetwork objects.

    Credits to https://djangosnippets.org/snippets/1862/
    """

    networks = []

    def __init__(self, addresses):
        """Create a new IpNetwork object for each address provided."""
        for address in addresses:
            self.networks.append(ipaddress.ip_network(address))

    def __contains__(self, address):
        """Check if the given address is contained in any of our Networks."""
        logger.debug('Checking address: "%s".', address)
        for network in self.networks:
            if ipaddress.ip_address(address) in network:
                return True
        return False


@configclass
def settings(config, env):
    """Configure security related settings."""
    # https://docs.djangoproject.com/en/stable/ref/settings/#secret-key
    config.SECRET_KEY = env("DJANGO_SECRET_KEY")
    # https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
    config.ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

    # SECURITY
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header
    config.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # https://docs.djangoproject.com/en/stable/ref/settings/#secure-ssl-redirect
    config.SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    # https://docs.djangoproject.com/en/stable/ref/settings/#session-cookie-secure
    config.SESSION_COOKIE_SECURE = config.SECURE_SSL_REDIRECT
    # https://docs.djangoproject.com/en/stable/ref/settings/#csrf-cookie-secure
    config.CSRF_COOKIE_SECURE = config.SECURE_SSL_REDIRECT
    # https://docs.djangoproject.com/en/stable/topics/security/#ssl-https
    # https://docs.djangoproject.com/en/stable/ref/settings/#secure-hsts-seconds
    config.SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60)
    # https://docs.djangoproject.com/en/stable/ref/settings/#secure-hsts-include-subdomains
    config.SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(config.SECURE_HSTS_SECONDS)
    # https://docs.djangoproject.com/en/stable/ref/settings/#secure-hsts-preload
    config.SECURE_HSTS_PRELOAD = bool(config.SECURE_HSTS_SECONDS)

    if env.bool("DJANGO_ENABLE_CORS_HANDLING", default=False):
        from corsheaders.defaults import default_headers

        config.INSTALLED_APPS = [
            "corsheaders",
        ] + config.INSTALLED_APPS
        config.CORS_ALLOW_ALL_ORIGINS = True

        config.MIDDLEWARE = [
            "corsheaders.middleware.CorsMiddleware",
        ] + config.MIDDLEWARE

        config.CORS_ALLOW_HEADERS = list(default_headers) + ["askanna-agent", "askanna-agent-version"]

    if config.DEBUG:
        # https://docs.djangoproject.com/en/stable/ref/settings/#internal-ips
        internal_ips = env.list("DJANGO_INTERNAL_IPS", default=["127.0.0.1"])
        if env.bool("USE_DOCKER", False):
            import socket

            _, _, ips = socket.gethostbyname_ex(socket.gethostname())
            internal_ips += [ip[:-1] + "1" for ip in ips]

        config.INTERNAL_IPS = IpNetworks(internal_ips)
