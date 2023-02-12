"""Authentication related settings."""

from .settings_decorator import configclass


@configclass
def settings(config, env):
    """Configure authentication related settings."""
    # AUTHENTICATION
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/stable/ref/settings/#authentication-backends
    config.AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
    ]
    # https://docs.djangoproject.com/en/stable/ref/settings/#auth-user-model
    config.AUTH_USER_MODEL = "account.User"
    # https://docs.djangoproject.com/en/stable/ref/settings/#login-redirect-url
    config.LOGIN_REDIRECT_URL = "/"

    # PASSWORDS
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/stable/ref/settings/#password-hashers
    config.PASSWORD_HASHERS = [
        # https://docs.djangoproject.com/en/stable/topics/auth/passwords/#using-argon2-with-django
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    ]
    # https://docs.djangoproject.com/en/stable/topics/auth/passwords/#password-validation
    config.AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    config.REST_AUTH_SERIALIZERS = {
        "LOGIN_SERIALIZER": "account.serializers.user.LoginSerializer",
        "USER_DETAILS_SERIALIZER": "account.serializers.user.UserSerializer",
    }
