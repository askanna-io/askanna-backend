from typing import Any, overload

from django.conf import settings

from core.models import Setting


@overload
def get_setting(name: str, return_type: type[str] = str, default: str | None = None) -> str:
    ...


@overload
def get_setting(name: str, return_type: type[bool], default: bool | None = None) -> bool:
    ...


@overload
def get_setting(name: str, return_type: type[int], default: int | None = None) -> int:
    ...


@overload
def get_setting(name: str, return_type: type[float], default: float | None = None) -> float:
    ...


@overload
def get_setting(name: str, return_type: type[Any], default: Any = None) -> Any:
    ...


def get_setting(name: str, return_type: type[Any] = str, default: Any = None) -> Any:
    """
    Retrieve configuration setting from database. If the setting is not found in the database, the value from
    django.conf.settings is returned when it's available. If the setting is also not found in django.conf.settings,
    the default svalue is returned.

    Args:
        name (str): name of the setting
        default (Any, optional): value to return when setting value is not found or is empty. Defaults to `None`.
        return_type (type[Any], optional): The value return type. Defaults to `str`.

    Returns:
        (Any): value of the setting
    """
    try:
        setting = Setting.objects.filter(deleted_at__isnull=True).get(name=name)
        value = setting.value
    except Setting.DoesNotExist:
        value = None

    if value is None or value == "":
        value = getattr(settings, name, default)

    if value is None:
        return value

    if return_type == bool:
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, str):
            if value.lower() in ["true", "1", "t", "y", "yes"]:
                value = True
            elif value.lower() in ["false", "0", "f", "n", "no"]:
                value = False

    if return_type in [bool, float, int, str] and isinstance(value, bool | float | int | str):
        try:
            return return_type(value)
        except ValueError:
            pass

    if isinstance(value, return_type):
        return value

    raise TypeError(
        f"The value of the setting '{name}' is not a {return_type.__name__} value, while return_type is set to "
        f"{return_type.__name__}."
    )
