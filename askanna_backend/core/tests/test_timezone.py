# -*- coding: utf-8 -*-
import unittest

from core.utils import is_valid_timezone


class TestTimezone(unittest.TestCase):
    def test_is_valid_timezone(self):
        self.assertEqual(is_valid_timezone("Europe/Amsterdam"), "Europe/Amsterdam")
        self.assertEqual(is_valid_timezone("Asia/Hong_Kong"), "Asia/Hong_Kong")
        self.assertEqual(is_valid_timezone("Australia/Darwin"), "Australia/Darwin")

    def test_is_valid_timezone_todefault(self):
        self.assertEqual(is_valid_timezone("Mars/Newtopia", "todefault"), "todefault")

    def test_is_valid_timezone_todefault_utc(self):
        self.assertEqual(is_valid_timezone("Mars/Newtopia"), "UTC")
