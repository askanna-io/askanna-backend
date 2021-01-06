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

from core.views import PermissionByActionMixin, SerializerByActionMixin
from users.serializers import (
    UserCreateSerializer,
    UserUpdateSerializer,
    UserSerializer,
    PasswordResetStatusSerializer,
    PasswordResetSerializer,
)
from users.permissions import IsOwnerOfUser, IsNotAlreadyMember

User = get_user_model()


class UserView(
    SerializerByActionMixin,
    PermissionByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = "short_uuid"
    serializer_class = UserSerializer

    permission_classes_by_action = {
        "list": [IsAdminUser],
        "create": [IsNotAlreadyMember],
        "update": [IsOwnerOfUser],
        "partial_update": [IsOwnerOfUser],
    }

    serializer_classes_by_action = {
        "post": UserCreateSerializer,
        "put": UserUpdateSerializer,
        "patch": UserUpdateSerializer,
    }
