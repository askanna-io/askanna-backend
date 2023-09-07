from rest_framework import exceptions, viewsets


class AskAnnaGenericViewSet(viewsets.GenericViewSet):
    def permission_denied(self, request, message=None, code=None):
        """
        If request is not permitted, we raise NotFound i.s.o. PermissionDenied or NotAuthenticated.
        We don't want to inform the other side that the resource exists.
        """
        raise exceptions.NotFound(detail=message, code=code)
