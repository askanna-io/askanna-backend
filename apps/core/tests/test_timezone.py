from core.utils import is_valid_timezone


def test_is_valid_timezone_valid():
    assert is_valid_timezone("Europe/Amsterdam") is True
    assert is_valid_timezone("Asia/Hong_Kong") is True
    assert is_valid_timezone("Australia/Darwin") is True


def test_is_valid_timezone_invalid():
    assert is_valid_timezone("Mars/Newtopia") is False
