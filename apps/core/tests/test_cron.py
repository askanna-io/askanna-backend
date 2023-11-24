import pytest

from core.utils import parse_cron_line


class TestCronLine:
    def test_parse_cron_line_str(self):
        cron_line = "* 1 * 2 *"
        assert parse_cron_line(cron_line) == cron_line

        cron_line = "* 1 * 2 * "
        assert parse_cron_line(cron_line) == cron_line.strip()

        cron_line = " * 1 * 2 * "
        assert parse_cron_line(cron_line) == cron_line.strip()

    def test_parse_cron_line_dict(self):
        cron_line = {"minute": 1, "hour": "*", "month": 12, "weekday": 5}
        assert parse_cron_line(cron_line) == "1 * * 12 5"

        cron_line = {"weekday": 1}
        assert parse_cron_line(cron_line) == "0 0 * * 1"

        cron_line = {"hour": "5", "month": 12, "weekday": "1-5"}
        assert parse_cron_line(cron_line) == "0 5 * 12 1-5"

        cron_line = {"minute": "*", "day": 5, "month": 8}
        assert parse_cron_line(cron_line) == "* 0 5 8 *"

    def test_parse_cron_line_alias(self):
        cron_line = "@yearly"
        assert parse_cron_line(cron_line) == "0 0 1 1 *"


class TestCronLineExceptions:
    def test_parse_cron_line_type_error(self):
        cron_line = ["* 1 * 2 *"]
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid cron_line type" in str(exc.value)

    def test_parse_cron_line_str_error(self):
        cron_line = "* 1 * 13 *"
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid parsed cron_line" in str(exc.value)

        cron_line = "* * * *"
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid parsed cron_line" in str(exc.value)

        cron_line = "1 2 3 4"
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid parsed cron_line" in str(exc.value)

        cron_line = "* * * * * * *"
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid parsed cron_line" in str(exc.value)

        cron_line = "does_not_exist"
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid parsed cron_line" in str(exc.value)

    def test_parse_cron_line_dict_error(self):
        cron_line = {"montly": 2}
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid cron_line key(s)" in str(exc.value)

        cron_line = {"weekday": 1, "montly": 2}
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid cron_line key(s)" in str(exc.value)

    def test_parse_cron_line_alias_error(self):
        cron_line = "@does_not_exist"
        with pytest.raises(ValueError) as exc:
            parse_cron_line(cron_line)
        assert "Invalid cron_line alias" in str(exc.value)
