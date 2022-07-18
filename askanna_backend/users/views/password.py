from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.serializers import PasswordResetSerializer, PasswordResetStatusSerializer


class PasswordResetView(GenericAPIView):
    """
    Calls Django Auth PasswordResetForm save method.
    Accepts the following POST parameters: email
    Returns the success/fail message.
    """

    serializer_class = PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("Password reset request has been processed.")},
            status=status.HTTP_200_OK,
        )


class PasswordResetStatus(viewsets.ViewSet):
    """
    Anyone can request this view as we are doing an password reset
    """

    serializer_class = PasswordResetStatusSerializer
    permission_classes = (AllowAny,)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data={
                "token": request.query_params.get("token"),
                "uid": request.query_params.get("uid"),
            },
            context={"request": self.request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
