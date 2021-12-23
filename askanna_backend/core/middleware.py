from functools import reduce
from django.db import connections
from django.utils.deprecation import MiddlewareMixin
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer


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

    def unauthorized_response(self, request, message):
        response = Response(
            {"detail": message},
            content_type="application/json",
            status=status.HTTP_401_UNAUTHORIZED,
        )
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        response.render()
        return response

    def process_request(self, request):
        # pre response
        authenticator = TokenAuthentication()
        user_auth_tuple = None
        try:
            user_auth_tuple = authenticator.authenticate(request)
        except exceptions.AuthenticationFailed as e:
            # the token could not be found or is invalid
            return self.unauthorized_response(request, e.detail)
        except exceptions.APIException:
            raise

        request.askanna = False

        if user_auth_tuple is not None:
            request.askanna = user_auth_tuple
            request.user, request.auth = user_auth_tuple
        else:
            request.auth = None
