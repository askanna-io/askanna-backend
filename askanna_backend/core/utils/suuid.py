import uuid as _uuid
from typing import Optional

# Inspiration for create suuid from uuid comes from https://pythonhosted.org/shorten/user/examples.html


def bx_encode(n: int, alphabet: str) -> str:
    """Encodes an integer 'n' in base 'len(alphabet)' with digits in 'alphabet'.

    Args:
        n (int): the integer to encode
        alphabet (str): the alphabet to use for encoding

    Raises:
        TypeError: if arguments are not of the correct type

    Returns:
        str: the encoded string
    """

    if not isinstance(n, int):
        raise TypeError("arg 'n' must be an integer")
    if not isinstance(alphabet, str):
        raise TypeError("arg 'alphabet' must be a string")

    base = len(alphabet)

    if n == 0:
        return alphabet[0]

    digits = []

    while n > 0:
        digits.append(alphabet[n % base])
        n = n // base

    digits.reverse()
    return "".join(digits)


def str_to_groups(string: str, group_size: int, n_groups: int) -> str:
    """Make a 'grouped string' from a string. The string is split into 'n_groups' groups of size 'group_size' and
    joined with a '-'.

    Args:
        string (str): the string to convert to suuid
        group_size (int): the size of each group
        n_groups (int): the number of groups

    Raises:
        ValueError: if the length of the string is not at least a multiple of 'group_size' and 'n_groups'

    Returns:
        str: a string in the suuid form
    """
    if len(string) < group_size * n_groups:
        raise ValueError("String is too short given the group size and number of groups")

    string_groups = [string[i : i + group_size] for i in range(0, len(string), group_size)]

    return "-".join(string_groups[:n_groups])


def create_suuid(uuid: Optional[_uuid.UUID] = None) -> str:
    """create_suuid will produce 16 character alphabetic tokens, split into 4 character groups. The format is:

        xxxx-xxxx-xxxx-xxxx

    When you provide a uuid, the suuid will be based on that uuid. If you don't provide a uuid, a new uuid will be
    generated.

    Args:
        uuid (uuid.UUID, optional): an uuid4 object

    Returns:
        str: a string in the suuid form
    """
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    token_length = 16
    group_size = 4

    n_groups = int(token_length / group_size)

    # Generate a random UUID if not given
    if not uuid:
        uuid = _uuid.uuid4()

    # Convert uuid to digits with the given alphabet
    token = bx_encode(int(uuid.hex, 16), alphabet)
    # Padding with the first symbol from 'alphabet' as needed to get the desired length
    token = token.rjust(token_length, alphabet[0])

    return str_to_groups(token, group_size, n_groups)
