# -*- coding: utf-8 -*-
import unittest

from core.utils import pretty_time_delta


class TestHumanizeDuration(unittest.TestCase):
    def test_pretty_time_delta(self):
        self.assertEqual(pretty_time_delta(0), "0 seconds")
        self.assertEqual(pretty_time_delta(1), "1 second")

        self.assertEqual(pretty_time_delta(60), "1 minute and 0 seconds")
        self.assertEqual(pretty_time_delta(61), "1 minute and 1 second")
        self.assertEqual(pretty_time_delta(62), "1 minute and 2 seconds")

        self.assertEqual(pretty_time_delta(120), "2 minutes and 0 seconds")
        self.assertEqual(pretty_time_delta(121), "2 minutes and 1 second")
        self.assertEqual(pretty_time_delta(122), "2 minutes and 2 seconds")

        self.assertEqual(pretty_time_delta(3660), "1 hour, 1 minute and 0 seconds")
        self.assertEqual(pretty_time_delta(3661), "1 hour, 1 minute and 1 second")
        self.assertEqual(pretty_time_delta(3662), "1 hour, 1 minute and 2 seconds")

        self.assertEqual(pretty_time_delta(7260), "2 hours, 1 minute and 0 seconds")
        self.assertEqual(pretty_time_delta(7261), "2 hours, 1 minute and 1 second")
        self.assertEqual(pretty_time_delta(7262), "2 hours, 1 minute and 2 seconds")

        self.assertEqual(pretty_time_delta(7321), "2 hours, 2 minutes and 1 second")
