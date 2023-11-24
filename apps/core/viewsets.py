from rest_framework import exceptions, viewsets


class AskAnnaGenericViewSet(viewsets.GenericViewSet):
    lookup_field = "suuid"

    def permission_denied(self, request, message=None, code=None):
        """
        If request is not permitted, we raise NotFound i.s.o. PermissionDenied. Except if the request is not
        (succesfully) authenticated, then we raise NotAuthenticated.

        We raise NotFound instead of PermissionDenied to prevent leaking information about the existence of objects.
        """
        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated()

        raise exceptions.NotFound(detail=message, code=code)
