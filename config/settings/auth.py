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
    config.LOGIN_REDIRECT_URL = "users:redirect"
    # https://docs.djangoproject.com/en/dev/ref/settings/#login-url
    config.LOGIN_URL = "account_login"

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
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        },
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    # django-allauth
    # ------------------------------------------------------------------------------
    config.ACCOUNT_ALLOW_REGISTRATION = env.bool(
        "DJANGO_ACCOUNT_ALLOW_REGISTRATION", True
    )
    # https://django-allauth.readthedocs.io/en/latest/configuration.html
    config.ACCOUNT_AUTHENTICATION_METHOD = "username"
    # https://django-allauth.readthedocs.io/en/latest/configuration.html
    config.ACCOUNT_EMAIL_REQUIRED = True
    # https://django-allauth.readthedocs.io/en/latest/configuration.html
    config.ACCOUNT_EMAIL_VERIFICATION = "optional"
    # https://django-allauth.readthedocs.io/en/latest/configuration.html
    config.ACCOUNT_ADAPTER = "askanna_backend.users.adapters.AccountAdapter"
    # https://django-allauth.readthedocs.io/en/latest/configuration.html
    config.SOCIALACCOUNT_ADAPTER = "askanna_backend.users.adapters.SocialAccountAdapter"
