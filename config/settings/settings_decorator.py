"""Helper decorators for better Django settings."""


class Config:
    """Data storage object for config settings."""


def configclass(func):
    """
    Convert a settings dictionary to be a data-object.

    Valid Django setting keys from the dict are set as attributes in the
    new config data object.

    This makes working with Django settings easier.
    now:
        config.THE_KEY

    before:
        config["THE_KEY"]
    """
    def wrapper(config, *args, **kwargs):
        """Wrap the decorated function."""
        # Create the Config object and set the valid settings.
        config_class = Config()
        for key, value in config.items():
            if key.isupper():
                setattr(config_class, key, value)

        func(config_class, *args, **kwargs)

        # Update original config with settings from the Config instance.
        config.update(
            **{
                key: value
                for key, value in config_class.__dict__.items()
                if key.isupper()
            }
        )

    return wrapper
