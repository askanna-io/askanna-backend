from django.utils.deprecation import MiddlewareMixin
from rest_framework import exceptions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


# Authentication in middleware
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
