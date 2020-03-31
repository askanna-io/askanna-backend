from collections import Mapping, Iterable
from uuid import uuid4

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


def bx_decode(string, alphabet, mapping=None):
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

    sum = 0

    for digit in string:
        try:
            sum = base * sum + mapping[digit]
        except KeyError:
            raise ValueError(
                "invalid literal for bx_decode with base %i: '%s'" % (base, digit)
            )

    return sum


def group(string, n):
    return [string[i : i + n] for i in range(0, len(string), n)]


class GoogleTokenGenerator(object):
    """\
   This will produce 16 character alphabetic revokation tokens similar
   to the ones Google uses for its application-specific passwords.

   Google tokens are of the form:

      xxxx-xxxx-xxxx-xxxx

   with alphabetic characters only.
   """

    alphabet = DEFAULT

    def create_token(self, key, uuid=None):
        token_length = 16
        group_size = 4
        groups = token_length / group_size

        # Generate a random UUID if not given
        if not uuid:
            uuid = uuid4()

        # Convert it to a number with the given alphabet,
        # padding with the 0-symbol as needed)
        token = bx_encode(int(uuid.hex, 16), self.alphabet)
        token = token.rjust(token_length, self.alphabet[0])

        return "-".join(group(token, group_size)[:groups])
