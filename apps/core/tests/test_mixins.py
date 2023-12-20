import pytest
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from core.mixins import ParserByActionMixin, PermissionByActionMixin


class PermissionView(PermissionByActionMixin, APIView):
    permission_classes = [IsAdminUser]
    permission_classes_by_action = {
        "create": [IsAdminUser, IsAuthenticated],
        "update": [IsAuthenticated, IsAdminUser],
    }


class ParserView(ParserByActionMixin, APIView):
    parser_classes = [JSONParser, MultiPartParser]
    parser_classes_by_action = {
        "create": [MultiPartParser, JSONParser],
        "update": [JSONParser, MultiPartParser],
    }


class TestParserByActionMixin:
    def test_get_parsers_create(self):
        test_view = ParserView()
        test_view.action = "create"

        assert [type(parser) for parser in test_view.get_parsers()] == [MultiPartParser, JSONParser]

    def test_get_parsers_update(self):
        test_view = ParserView()
        test_view.action = "update"

        assert [type(parser) for parser in test_view.get_parsers()] == [JSONParser, MultiPartParser]

    def test_get_parsers_remove(self):
        test_view = ParserView()
        test_view.action = "remove"  # Note: this action is not defined in the 'parser_classes_by_action' dict

        assert [type(parser) for parser in test_view.get_parsers()] == [JSONParser, MultiPartParser]

    def test_get_parsers_default(self):
        test_view = ParserView()
        test_view.action = None

        assert [type(parser) for parser in test_view.get_parsers()] == [JSONParser, MultiPartParser]

    def test_view_without_parser_classes_by_action(self):
        class TestView(ParserByActionMixin, APIView):
            pass

        test_view = TestView()

        with pytest.raises(AssertionError):
            test_view.get_parsers()


class TestPermissionByActionMixin:
    def test_get_permission_create(self):
        test_view = PermissionView()
        test_view.action = "create"

        assert [type(permission) for permission in test_view.get_permissions()] == [IsAdminUser, IsAuthenticated]

    def test_get_permission_update(self):
        test_view = PermissionView()
        test_view.action = "update"

        assert [type(permission) for permission in test_view.get_permissions()] == [IsAuthenticated, IsAdminUser]

    def test_get_permission_remove(self):
        test_view = PermissionView()
        test_view.action = "remove"  # Note: this action is not defined in the 'parser_classes_by_action' dict

        assert [type(permission) for permission in test_view.get_permissions()] == [IsAdminUser]

    def test_get_permission_no_action(self):
        test_view = PermissionView()
        test_view.action = None

        with pytest.raises(AssertionError):
            test_view.get_permissions()

    def test_view_without_permission_classes_by_action(self):
        class TestView(PermissionByActionMixin, APIView):
            pass

        test_view = TestView()

        with pytest.raises(AssertionError):
            test_view.get_permissions()
