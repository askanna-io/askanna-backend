# -*- coding: utf-8 -*-
from collections.abc import Mapping
import datetime
import json
import os
import uuid

import croniter
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.db.models.query import QuerySet
from django.urls import register_converter
from django.utils import timezone
import filetype
import magic
import pytz
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# From https://pythonhosted.org/shorten/user/examples.html


HEX = "0123456789abcdef"
DEFAULT = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DISSIMILAR = "23456790ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
URLSAFE = "0123456789ABCEDFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_~"
URLSAFE_DISSIMILAR = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz-_~"


def bx_encode(n, alphabet):
    """
    Encodes an integer :attr:`n` in base ``len(alphabet)`` with
    digits in :attr:`alphabet`.

    ::
        # 'ba'
        bx_encode(3, 'abc')
    :param n:            a positive integer.
    :param alphabet:     a 0-based iterable.
    """

    if not isinstance(n, int):
        raise TypeError("an integer is required")

    base = len(alphabet)

    if n == 0:
        return alphabet[0]

    digits = []

    while n > 0:
        digits.append(alphabet[n % base])
        n = n // base

    digits.reverse()
    return "".join(digits)


def bx_decode(string, alphabet=DEFAULT, mapping=None):
    """
    Transforms a string in :attr:`alphabet` to an integer.

    If :attr:`mapping` is provided, each key must map to its
    positional value without duplicates.
    ::
        mapping = {'a': 0, 'b': 1, 'c': 2}
        # 3
        bx_decode('ba', 'abc', mapping)

    :param string:       a string consisting of key from `alphabet`.
    :param alphabet:     a 0-based iterable.

    :param mapping:      a :class:`Mapping <collection.Mapping>`. If `None`,
                            the inverse of `alphabet` is used, with values mapped
                            to indices.
    """

    mapping = mapping or dict([(d, i) for (i, d) in enumerate(alphabet)])
    base = len(alphabet)

    if not string:
        raise ValueError("string cannot be empty")

    if not isinstance(mapping, Mapping):
        raise TypeError("a Mapping is required")

    sum_of_string = 0

    for digit in string:
        try:
            sum_of_string = base * sum_of_string + mapping[digit]
        except KeyError:
            raise ValueError(
                "invalid literal for bx_decode with base %i: '%s'" % (base, digit)
            )

    return sum_of_string


def group(string, n):
    return [string[i : i + n] for i in range(0, len(string), n)]


class GoogleTokenGenerator:
    """
    This will produce 16 character alphabetic revokation tokens similar
    to the ones Google uses for its application-specific passwords.

    Google tokens are of the form:

        xxxx-xxxx-xxxx-xxxx

    with alphabetic characters only.
    """

    alphabet = DEFAULT

    def create_token(self, uuid_in=None):
        token_length = 16
        group_size = 4
        groups = int(token_length / group_size)

        # Generate a random UUID if not given
        if not uuid_in:
            uuid_in = uuid.uuid4()

        # Convert it to a number with the given alphabet,
        # padding with the 0-symbol as needed)
        token = bx_encode(int(uuid_in.hex, 16), self.alphabet)
        token = token.rjust(token_length, self.alphabet[0])

        return "-".join(group(token, group_size)[:groups])


class ShortUUIDConverter:
    regex = r"[0-9a-zA-Z]{4}\-[0-9a-zA-Z]{4}\-[0-9a-zA-Z]{4}\-[0-9a-zA-Z]{4}"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(ShortUUIDConverter, "shortuuid")


def get_config_from_string(config_yml: str) -> dict:
    """
    Given a yml string, load this into dict
    """
    try:
        config = load(config_yml, Loader=Loader)
    except:  # noqa
        config = None
    return config


def get_config(filename: str) -> dict:
    """
    Given a filepath, load it and return the intepretated yml
    """
    return get_config_from_string(open(os.path.expanduser(filename), "r"))


def validate_cron_line(cron_line: str) -> bool:
    """
    We validate the cron expression with croniter
    """
    try:
        return croniter.croniter.is_valid(cron_line)
    except AttributeError:
        return False


def parse_cron_line(cron_line: str) -> str:
    """
    parse incoming cron definition
    if it is valid, then return the cron_line, otherwise a None
    """

    if isinstance(cron_line, str):
        # we deal with cron strings
        # first check whether we need to make a "translation" for @strings

        alias_mapping = {
            "@midnight": "0 0 * * *",
            "@yearly": "0 0 1 1 *",
            "@annually": "0 0 1 1 *",
            "@monthly": "0 0 1 * *",
            "@weekly": "0 0 * * 0",
            "@daily": "0 0 * * *",
            "@hourly": "0 * * * *",
        }
        cron_line = alias_mapping.get(cron_line.strip(), cron_line.strip())

    elif isinstance(cron_line, dict):
        # we deal with dictionary
        # first check whether we have valid keys, if one invalid key is found, return None
        valid_keys = set(["minute", "hour", "day", "month", "weekday"])
        invalid_keys = set(cron_line.keys()) - valid_keys
        if len(invalid_keys):
            return None
        cron_line = "{minute} {hour} {day} {month} {weekday}".format(
            minute=cron_line.get("minute", "0"),
            hour=cron_line.get("hour", "0"),
            day=cron_line.get("day", "*"),
            month=cron_line.get("month", "*"),
            weekday=cron_line.get("weekday", "*"),
        )

    if not validate_cron_line(cron_line):
        return None

    return cron_line


def parse_cron_schedule(schedule: list):
    """
    Determine which format it has, it can be one of the following:
    - * * * * *  (m, h, d, m, weekday)
    - @annotation (@yearly, @annually, @monthly, @weekly, @daily, @hourly)
    - dict (k,v with: minute,hour,day,month,weekday)
    """

    for cron_line in schedule:
        yield cron_line, parse_cron_line(cron_line)


def find_last_modified(directory, filelist):
    latest_modified = datetime.datetime(1970, 1, 1, 0, 0, 0)
    sub_dir_files = filter(lambda x: x["parent"].startswith(directory), filelist)
    for f in sub_dir_files:
        if f.get("last_modified") > latest_modified:
            latest_modified = f.get("last_modified")

    return latest_modified


# File mimetype detection logic


def is_jsonfile(filepath) -> bool:
    """
    Determine whether we are dealing with a JSON file
    returns True/False
    """

    try:
        json.load(open(filepath))
    except json.decoder.JSONDecodeError:
        return False
    return True


def detect_file_mimetype(filepath):
    """
    Use libmagic to determine what file we find on `filepath`.
    We return either None or the found mimetype
    """
    detected_mimetype = None

    try:
        detected_mimetype = magic.from_file(filepath, mime=True)
    except FileNotFoundError as e:
        # something terrible happened, we stored the file but it cannot be found
        raise e

    if detected_mimetype:
        if detected_mimetype == "text/plain":
            # try to detect JSON
            if is_jsonfile(filepath):
                detected_mimetype = "application/json"
    else:
        kind = filetype.guess(filepath)
        if kind:
            detected_mimetype = kind.mime

    return detected_mimetype


# date timezone validation
def is_valid_timezone(timezone, default=settings.TIME_ZONE):
    """
    Validate whether the timezone specified is a valid one
    If not, return the default timezone.
    """
    if timezone not in pytz.all_timezones:
        return default
    return timezone


# settings management
def get_setting_from_database(name: str, default=None):
    """
    Retrieve configuration setting from database (if set)
    Otherwise fall back to
    """
    # import model here because of circular import (models is also using .utils)
    from core.models import Setting

    try:
        setting = Setting.objects.get(name=name)
    except ObjectDoesNotExist:
        return default
    else:
        return setting.value


def is_valid_email(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    else:
        return True


# object removal
def remove_objects(queryset, ttl_hours: int = 1):
    """
    queryset: Queryset containing all objects, also the ones not to delete
    ttl_hours: we only delete objects older than `ttl_hours` old.
    """
    if not isinstance(queryset, QuerySet):
        raise Exception("Given queryset is not a Django Queryset")

    remove_ttl = get_setting_from_database(
        name="OBJECT_REMOVAL_TTL_HOURS", default=ttl_hours
    )
    remove_ttl_mins = int(float(remove_ttl) * 60.0)

    older_than = timezone.now() - datetime.timedelta(minutes=remove_ttl_mins)

    for obj in queryset.filter(deleted__lte=older_than):
        obj.delete()


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
        return "%s, %s, %s and %s" % (
            plurify(days, "day", "days"),
            plurify(hours, "hour", "hours"),
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    elif hours > 0:
        return "%s, %s and %s" % (
            plurify(hours, "hour", "hours"),
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    elif minutes > 0:
        return "%s and %s" % (
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    else:
        return "%s" % (plurify(seconds, "second", "seconds"),)


def flatten(t):
    return [item for sublist in t for item in sublist]
