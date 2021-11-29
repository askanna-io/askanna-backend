from rest_framework.authentication import BaseAuthentication


class PassthroughAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # set user from old request
        user = request._request.user
        auth = None
        if hasattr(request._request, "auth"):
            auth = request._request.auth

        if not request._request.askanna:
            return None

        return user, auth

    def authenticate_header(self, request):
        return "Passtrough"
