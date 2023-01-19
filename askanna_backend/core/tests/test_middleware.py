import io
from unittest import mock

from django.test import override_settings
from rest_framework.test import APITestCase
from users.models import User


class SqlPrintMiddlewareTest(APITestCase):
    @override_settings(DEBUG=True, DEBUG_SQL=True)
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_sql_print(self, mock_stdout):
        user = User.objects.create_user("john", "john@example.com", "password")
        self.client.get("/v1/auth/user/", HTTP_AUTHORIZATION="Token %s" % user.auth_token.key)

        assert "SELECT" in mock_stdout.getvalue()
        assert "TOTAL QUERIES" in mock_stdout.getvalue()

    @override_settings(DEBUG=False, DEBUG_SQL=False)
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_sql_print_off(self, mock_stdout):
        user = User.objects.create_user("john", "john@example.com", "password")
        self.client.get("/v1/auth/user/", HTTP_AUTHORIZATION="Token %s" % user.auth_token.key)

        assert "SELECT" not in mock_stdout.getvalue()
        assert "TOTAL QUERIES" not in mock_stdout.getvalue()
