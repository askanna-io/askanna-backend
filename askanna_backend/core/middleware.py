from functools import reduce
from django.db import connections
from django.utils.deprecation import MiddlewareMixin
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


class DebugDBConnectionMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        # pre response code

        # the response
        response = self.get_response(request)

        # post response code
        view = request.path
        method = request.method.upper()
        print(
            method,
            view,
            str(reduce(lambda n, name: n + len(connections[name].queries), connections, 0)),
            "queries",
            str(
                reduce(
                    lambda n, name: n + reduce(lambda n, y: float(y["time"]), connections[name].queries, 0.0),
                    connections,
                    0.0,
                )
                * 1000
            ),
            "ms",
        )
        for con in connections:
            for q in connections[con].queries:
                print(q)

        return response


# authentication in middleware
class TokenAuthenticationMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        # pre response
        authenticator = TokenAuthentication()
        try:
            user_auth_tuple = authenticator.authenticate(request)
        except exceptions.APIException:
            raise

        request.askanna = False

        if user_auth_tuple is not None:
            request.askanna = user_auth_tuple
            request.user, request.auth = user_auth_tuple
        else:
            request.auth = None
