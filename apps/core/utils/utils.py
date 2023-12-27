import zoneinfo

import croniter
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from jinja2 import Environment, select_autoescape


def parse_string(string: str, variables: dict) -> str:
    env = Environment(variable_start_string="${", variable_end_string="}", autoescape=select_autoescape())
    template = env.from_string(string)
    return template.render(variables)


def validate_cron_line(cron_line: str) -> bool:
    """
    We validate the cron expression with croniter
    """
    try:
        return croniter.croniter.is_valid(cron_line)
    except AttributeError:
        return False


def parse_cron_line(cron_line: str | dict) -> str:
    """
    Parse raw cron line and if it's valid return the cron definition. If it's not valid, raise a ValueError.

    The parses determines which format the raw cron line is. It can be one of the following:
    - "* * * * *"  (m, h, d, m, weekday)
    - "@string" (@yearly, @annually, @daily, @hourly, etc.)
    - dict (key, value with keys: minute, hour, day, month, weekday)
    """

    if isinstance(cron_line, str):
        cron_line_parsed = cron_line.strip()

        if cron_line_parsed.startswith("@"):
            # "translate" @string variants
            alias_mapping = {
                "@midnight": "0 0 * * *",
                "@yearly": "0 0 1 1 *",
                "@annually": "0 0 1 1 *",
                "@monthly": "0 0 1 * *",
                "@weekly": "0 0 * * 0",
                "@daily": "0 0 * * *",
                "@hourly": "0 * * * *",
            }
            cron_line_parsed = alias_mapping.get(cron_line_parsed, None)

            if cron_line_parsed is None:
                raise ValueError(
                    "Invalid cron_line alias `%s`. Supported aliases are `%s`.",
                    cron_line,
                    ", ".join(alias_mapping.keys()),
                )

    elif isinstance(cron_line, dict):
        # Check whether we have valid keys, if one invalid key is found, raise an error
        valid_keys = {"minute", "hour", "day", "month", "weekday"}
        invalid_keys = set(cron_line.keys()) - valid_keys

        if len(invalid_keys):
            raise ValueError(
                "Invalid cron_line key(s) are used `%s`. Supported keys are `{}`.",
                ", ".join(invalid_keys),
                ", ".join(valid_keys),
            )

        cron_line_parsed = "{minute} {hour} {day} {month} {weekday}".format(
            minute=cron_line.get("minute", "0"),
            hour=cron_line.get("hour", "0"),
            day=cron_line.get("day", "*"),
            month=cron_line.get("month", "*"),
            weekday=cron_line.get("weekday", "*"),
        )

    else:
        raise ValueError(
            "Invalid cron_line type `%s`. Supported types are `str` and `dict`.",
            type(cron_line).__name__,
        )

    if validate_cron_line(cron_line_parsed):
        return cron_line_parsed

    raise ValueError(
        "Invalid parsed cron_line `%s`.\n  cron_line: `%s`\n  parsed_cron_line: `%s`.",
        cron_line,
        cron_line,
        cron_line_parsed,
    )


def is_valid_timezone(timezone: str) -> bool:
    """Validate whether the timezone specified is a valid one"""
    return timezone in zoneinfo.available_timezones()


def is_valid_email(email: str) -> bool:
    """Validate whether the email specified is a valid one"""
    try:
        validate_email(email)
    except ValidationError:
        return False
    else:
        return True


def pretty_time_delta(seconds: int) -> str:
    """
    Transforms an integer which represents duration into a human readable string
    """
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    def plurify(amount, single, plural):
        if amount == 1:
            return f"{amount} {single}"
        return f"{amount} {plural}"

    if days > 0:
        return "{}, {}, {} and {}".format(
            plurify(days, "day", "days"),
            plurify(hours, "hour", "hours"),
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    if hours > 0:
        return "{}, {} and {}".format(
            plurify(hours, "hour", "hours"),
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    if minutes > 0:
        return "{} and {}".format(
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )

    return "{}".format(plurify(seconds, "second", "seconds"))


def flatten(t):
    return [item for sublist in t for item in sublist]
