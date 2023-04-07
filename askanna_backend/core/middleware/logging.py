"""
Inspired by code from angysmark, you can check the original gist at:
https://gist.github.com/angysmark/bbeeb58608c90901d40b052aee4c5f2b
"""
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.db import connection


class DebugSqlPrintMiddleware:
    def __init__(self, get_response):
        if settings.DEBUG_SQL is False:
            raise MiddlewareNotUsed
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            settings.DEBUG_SQL is False
            or len(connection.queries) == 0
            or request.path_info.startswith(settings.MEDIA_URL)
            or "/admin/jsi18n/" in request.path_info
        ):
            return response

        print(f'\n\033[1;35mSQL Queries for\033[1;34m "{request.method} {request.path_info}"\033[0m\n')  # noqa: T201
        total_time = 0.0
        for query in connection.queries:
            nice_sql = query["sql"].replace('"', "").replace(",", ", ")
            sql = "\033[1;31m[{}]\033[0m {}".format(query["time"], nice_sql)
            total_time = total_time + float(query["time"])
            print(f"{sql}\n")  # noqa: T201

        print(f"\033[1;32mTOTAL QUERIES: {len(connection.queries)}\033[0m")  # noqa: T201
        print(f"\033[1;32mTOTAL TIME: {str(total_time)} seconds\033[0m\n")  # noqa: T201

        return response
