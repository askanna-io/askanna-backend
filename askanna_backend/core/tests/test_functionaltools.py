import unittest

from core.utils import flatten, is_valid_email


class TestFunctionalTools(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(flatten([[1, 2], [3], [4, 5, 6], [7], [8]]), [1, 2, 3, 4, 5, 6, 7, 8])


class TestIsValidEmail(unittest.TestCase):
    def test_is_valid_email(self):
        assert is_valid_email("hello@example.com") is True
        assert is_valid_email("hello@example.cloud") is True
        assert is_valid_email("hello") is False
        assert is_valid_email("hello@") is False
