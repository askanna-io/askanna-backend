# -*- coding: utf-8 -*-
from collections.abc import Mapping
import datetime
import json
import os
import uuid

from django.urls import register_converter
import filetype
import magic
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


def get_config(filename: str) -> dict:
    # FIXME: put this into a general askanna-utils to read askanna.yml
    config = load(open(os.path.expanduser(filename), "r"), Loader=Loader)
    return config


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
