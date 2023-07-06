import pytest
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from .models import BaseCursorPaginationModel, NullableCursorPaginationModel
from core import pagination

factory = APIRequestFactory()
pytestmark = pytest.mark.django_db


class BaseCursorPaginationTestCase(TestCase):
    def get_pages(self, url):
        """
        Given a URL return a tuple of:

        (previous page, current page, next page, previous url, next url)
        """
        request = Request(factory.get(url))
        queryset = self.pagination.paginate_queryset(self.queryset, request)
        current = [item.idx for item in queryset]

        next_url = self.pagination.get_next_link()
        previous_url = self.pagination.get_previous_link()

        if next_url is not None:
            request = Request(factory.get(next_url))
            queryset = self.pagination.paginate_queryset(self.queryset, request)
            next = [item.idx for item in queryset]
        else:
            next = None

        if previous_url is not None:
            request = Request(factory.get(previous_url))
            queryset = self.pagination.paginate_queryset(self.queryset, request)
            previous = [item.idx for item in queryset]
        else:
            previous = None

        return (previous, current, next, previous_url, next_url)


class TestCursorPaginationOnCreatedAt(BaseCursorPaginationTestCase):
    """
    Unit tests for CursorPagination with ordering on a nullable field.
    """

    def setUp(self):
        class ExamplePagination(pagination.CursorPagination):
            page_size = 3

        self.pagination = ExamplePagination()
        data = [3, 4, 5, 1, 2, 3, 4, 6]
        for idx in data:
            BaseCursorPaginationModel.objects.create(idx=idx)

        self.queryset = BaseCursorPaginationModel.objects.all()

    def test_ascending(self):
        self.pagination.ordering = "created_at"
        (previous, current, next, previous_url, next_url) = self.get_pages("/")

        assert previous is None
        assert current == [3, 4, 5]
        assert next == [1, 2, 3]
        assert previous_url is None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [3, 4, 5]
        assert current == [1, 2, 3]
        assert next == [4, 6]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [1, 2, 3]
        assert current == [4, 6]
        assert next is None
        assert previous_url is not None
        assert next_url is None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous == [3, 4, 5]
        assert current == [1, 2, 3]
        assert next == [4, 6]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous is None
        assert current == [3, 4, 5]
        assert next == [1, 2, 3]
        assert previous_url is None
        assert next_url is not None

    def test_descending(self):
        self.pagination.ordering = "-created_at"
        (previous, current, next, previous_url, next_url) = self.get_pages("/")

        assert previous is None
        assert current == [6, 4, 3]
        assert next == [2, 1, 5]
        assert previous_url is None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [6, 4, 3]
        assert current == [2, 1, 5]
        assert next == [4, 3]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [2, 1, 5]
        assert current == [4, 3]
        assert next is None
        assert previous_url is not None
        assert next_url is None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous == [6, 4, 3]
        assert current == [2, 1, 5]
        assert next == [4, 3]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous is None
        assert current == [6, 4, 3]
        assert next == [2, 1, 5]
        assert previous_url is None
        assert next_url is not None


class TestCursorPaginationWithNulls(BaseCursorPaginationTestCase):
    """
    Unit tests for CursorPagination with ordering on a nullable field.
    """

    def setUp(self):
        class ExamplePagination(pagination.CursorPagination):
            page_size = 1

        self.pagination = ExamplePagination()
        data = [None, None, 3, 4]
        for idx in data:
            NullableCursorPaginationModel.objects.create(idx=idx)

        self.queryset = NullableCursorPaginationModel.objects.all()

    def test_ascending(self):
        self.pagination.ordering = "idx"
        (previous, current, next, previous_url, next_url) = self.get_pages("/")

        assert previous is None
        assert current == [3]
        assert next == [4]
        assert previous_url is None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [3]
        assert current == [4]
        assert next == [None]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [4]
        assert current == [None]
        assert next == [None]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [None]
        assert current == [None]
        assert next is None
        assert previous_url is not None
        assert next_url is None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous == [4]
        assert current == [None]
        assert next == [None]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous == [3]
        assert current == [4]
        assert next == [None]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous is None
        assert current == [3]
        assert next == [4]
        assert previous_url is None
        assert next_url is not None

    def test_descending(self):
        self.pagination.ordering = "-idx"
        (previous, current, next, previous_url, next_url) = self.get_pages("/")

        assert previous is None
        assert current == [None]
        assert next == [None]
        assert previous_url is None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [None]
        assert current == [None]
        assert next == [4]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [None]
        assert current == [4]
        assert next == [3]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(next_url)

        assert previous == [4]
        assert current == [3]
        assert next is None
        assert previous_url is not None
        assert next_url is None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous == [None]
        assert current == [4]
        assert next == [3]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous == [None]
        assert current == [None]
        assert next == [4]
        assert previous_url is not None
        assert next_url is not None

        (previous, current, next, previous_url, next_url) = self.get_pages(previous_url)

        assert previous is None
        assert current == [None]
        assert next == [None]
        assert previous_url is None
        assert next_url is not None
