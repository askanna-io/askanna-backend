"""
Inspired by code from angysmark, you can check the original gist at:
https://gist.github.com/angysmark/bbeeb58608c90901d40b052aee4c5f2b
"""
import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.db import connection

logger = logging.getLogger(__name__)


class DebugSqlMiddleware:
    def __init__(self, get_response):
        if settings.DEBUG_SQL is False:
            raise MiddlewareNotUsed
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            settings.DEBUG_SQL is False
            or len(connection.queries) == 0
            or "/admin/jsi18n/" in request.path_info
            or (
                len(connection.queries) == 2
                and connection.queries[0]["sql"] == "BEGIN"
                and connection.queries[-1]["sql"] == "COMMIT"
            )
        ):
            return response

        logger.info('\n\033[1;35mSQL Queries for\033[1;34m "%s %s"\033[0m\n', request.method, request.path_info)
        total_time = 0.0

        for query in connection.queries:
            nice_sql = query["sql"].replace('"', "").replace(",", ", ")
            sql = f"\033[1;31m[{query['time']}]\033[0m {nice_sql}"
            total_time = total_time + float(query["time"])
            logger.info("%s\n", sql)

        number_of_queries = len(connection.queries)
        if connection.queries[0]["sql"] == "BEGIN" and connection.queries[-1]["sql"] == "COMMIT":
            number_of_queries = number_of_queries - 2

        logger.info("\033[1;32mTOTAL QUERIES: %s\033[0m", number_of_queries)
        logger.info("\033[1;32mTOTAL TIME:    %s seconds\033[0m\n", total_time)

        return response
