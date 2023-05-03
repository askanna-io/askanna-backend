from core.models import Setting


def get_setting_from_database(
    name: str, default: str | int | bool | None = None, return_type: type[str | int | bool] = str
) -> str | int | bool | None:
    """
    Retrieve configuration setting from database

    Args:
        name (str): name of the setting
        default (str, int, bool, optional): value to return when setting value is not found or is empty.
            Defaults to None.
        return_type (Type[str, int, bool], optional): Optionally, the value return type. Defaults to str.

    Returns:
        (str | int | bool | None): value of the setting
    """
    try:
        setting = Setting.objects.get(name=name)
    except Setting.DoesNotExist:
        value = default
    else:
        value = setting.value or default

    if return_type == bool:
        if type(value) == int:
            value = str(value)
        if type(value) == str:
            if value.lower() in ["true", "1", "t", "y", "yes"]:  # type: ignore
                value = True
            elif value.lower() in ["false", "0", "f", "n", "no"]:  # type: ignore
                value = False
        if type(value) != bool:
            raise TypeError(
                f"The value of the setting '{name}' is not a boolean value, while return type is set to bool."
            )

    if return_type == int:
        if type(value) in [str, bool]:
            try:
                value = int(value)  # type: ignore
            except ValueError:
                pass
        if type(value) != int:
            raise TypeError(
                f"The value of the setting '{name}' is not an integer value, while return type is set to int."
            )

    return value
