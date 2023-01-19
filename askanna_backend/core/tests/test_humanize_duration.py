import unittest

from core.utils import pretty_time_delta


class TestHumanizeDuration(unittest.TestCase):
    def test_pretty_time_delta(self):
        assert pretty_time_delta(0) == "0 seconds"
        assert pretty_time_delta(1) == "1 second"

        assert pretty_time_delta(60) == "1 minute and 0 seconds"
        assert pretty_time_delta(61) == "1 minute and 1 second"
        assert pretty_time_delta(62) == "1 minute and 2 seconds"

        assert pretty_time_delta(120) == "2 minutes and 0 seconds"
        assert pretty_time_delta(121) == "2 minutes and 1 second"
        assert pretty_time_delta(122) == "2 minutes and 2 seconds"

        assert pretty_time_delta(3660) == "1 hour, 1 minute and 0 seconds"
        assert pretty_time_delta(3661) == "1 hour, 1 minute and 1 second"
        assert pretty_time_delta(3662) == "1 hour, 1 minute and 2 seconds"
        assert pretty_time_delta(3720) == "1 hour, 2 minutes and 0 seconds"

        assert pretty_time_delta(7260) == "2 hours, 1 minute and 0 seconds"
        assert pretty_time_delta(7261) == "2 hours, 1 minute and 1 second"
        assert pretty_time_delta(7262) == "2 hours, 1 minute and 2 seconds"
        assert pretty_time_delta(7320) == "2 hours, 2 minutes and 0 seconds"

        assert pretty_time_delta(86400) == "1 day, 0 hours, 0 minutes and 0 seconds"
        assert pretty_time_delta(86401) == "1 day, 0 hours, 0 minutes and 1 second"
        assert pretty_time_delta(86402) == "1 day, 0 hours, 0 minutes and 2 seconds"
        assert pretty_time_delta(86460) == "1 day, 0 hours, 1 minute and 0 seconds"
        assert pretty_time_delta(86461) == "1 day, 0 hours, 1 minute and 1 second"
        assert pretty_time_delta(86520) == "1 day, 0 hours, 2 minutes and 0 seconds"
        assert pretty_time_delta(90000) == "1 day, 1 hour, 0 minutes and 0 seconds"
