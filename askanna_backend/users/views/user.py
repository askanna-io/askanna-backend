from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView, RedirectView, UpdateView
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from rest_framework.decorators import action
from rest_framework import mixins, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from users.serializers import (
    UserCreateSerializer,
    UserSerializer,
    PasswordResetStatusSerializer,
    PasswordResetSerializer,
)
from users.permissions import IsOwnerOfUser, IsNotAlreadyMember

User = get_user_model()


class UserView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    permission_classes_by_action = {
        "list": [IsAdminUser],
        "create": [IsNotAlreadyMember],
        "update": [IsOwnerOfUser],
        "partial_update": [IsOwnerOfUser],
    }

    def get_serializer_class(self):
        """
        Return different serializer class for create
        """
        if self.request.method.upper() in ["POST"]:
            return UserCreateSerializer
        return self.serializer_class

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]
