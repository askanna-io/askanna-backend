import unittest

from core.utils import flatten


class TestFunctionalTools(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(flatten([[1, 2], [3], [4, 5, 6], [7], [8]]), [1, 2, 3, 4, 5, 6, 7, 8])
