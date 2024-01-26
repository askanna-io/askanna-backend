from rest_framework import exceptions, viewsets


class AskAnnaGenericViewSet(viewsets.GenericViewSet):
    lookup_field = "suuid"
    lookup_value_regex = "[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}"

    def permission_denied(self, request, message=None, code=None):
        """
        If request is not permitted, we raise NotFound i.s.o. PermissionDenied. Except if the request is not
        (succesfully) authenticated, then we raise NotAuthenticated.

        We raise NotFound instead of PermissionDenied to prevent leaking information about the existence of objects.
        """
        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated()

        raise exceptions.NotFound(detail=message, code=code)

    @property
    def member_of_workspaces(self):
        from account.models.membership import MSP_WORKSPACE

        return (
            self.request.user.active_memberships.filter(object_type=MSP_WORKSPACE).values_list(
                "object_uuid", flat=True
            )
            if self.request.user.is_active
            else []
        )
