from functools import reduce
from django.db import connections


class DebugDBConnectionMiddelware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # pre response code

        # the response
        response = self.get_response(request)

        # post response code
        view = request.path
        print(
            view,
            str(
                reduce(
                    lambda n, name: n + len(connections[name].queries), connections, 0
                )
            ),
            "queries",
            str(
                reduce(
                    lambda n, name: n
                    + reduce(
                        lambda n, y: float(y["time"]), connections[name].queries, 0.0
                    ),
                    connections,
                    0.0,
                )
                * 1000
            ),
            "ms",
        )
        # for con in connections:
        #     for q in connections[con].queries:
        #         print(q)

        return response
