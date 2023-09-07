from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.serializers.user import (
    PasswordResetSerializer,
    PasswordResetTokenStatusSerializer,
    UserSerializer,
)


class UserDetailsView(RetrieveAPIView):
    """
    Get info about the authenticated user
    """

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(
    responses={202: None},
)
class PasswordResetView(GenericAPIView):
    """
    Post a request to reset the password for an account
    """

    serializer_class = PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_202_ACCEPTED)


@extend_schema(
    parameters=[
        OpenApiParameter("token", str, OpenApiParameter.QUERY, description="Password reset token"),
        OpenApiParameter("uid", str, OpenApiParameter.QUERY, description="User UID"),
    ],
    responses={200: PasswordResetTokenStatusSerializer},
)
class PasswordResetTokenStatusView(viewsets.ViewSet):
    """
    Check if a password reset token is valid
    """

    permission_classes = (AllowAny,)

    def retrieve(self, request, *args, **kwargs):
        data = {
            "token": request.query_params.get("token"),
            "uid": request.query_params.get("uid"),
        }
        serializer = PasswordResetTokenStatusSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
