"""Authentication related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure authentication related settings."""
    # AUTHENTICATION
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
    config.AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    ]
    # https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
    config.AUTH_USER_MODEL = "users.User"
    # https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
    config.LOGIN_REDIRECT_URL = "/"

    # PASSWORDS
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
    config.PASSWORD_HASHERS = [
        # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    ]
    # https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
    config.AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    config.REST_AUTH_SERIALIZERS = {"USER_DETAILS_SERIALIZER": "users.serializers.UserSerializer"}

    config.SWAGGER_SETTINGS = {
        "SECURITY_DEFINITIONS": {
            "Token": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
            }
        },
    }
