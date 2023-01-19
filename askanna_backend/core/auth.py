from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication


class PassthroughAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Set user from previous request
        user = request._request.user
        auth = None
        if hasattr(request._request, "auth"):
            auth = request._request.auth

        if not request._request.askanna:
            return None

        return user, auth

    def authenticate_header(self, request):
        return "Passthrough"


class PassthroughAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "core.auth.PassthroughAuthentication"
    name = "TokenAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Prefix the value with 'Token ' to authorize your requests",
        }
