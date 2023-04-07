from account.models import Membership, User
from core.views import get_object_or_404
from django.http import Http404
from rest_framework import viewsets
from rest_framework.response import Response


class UpdateModelWithoutPartialUpateMixin:
    """
    Update a model instance without offering the 'partial_update' method.

    Source: this mixin is based on the 'UpdateModelMixin' from the 'rest_framework.mixins' module.
    """

    def update(self, request, *args, **kwargs):
        instance = self.get_object()  # type: ignore
        serializer = self.get_serializer(instance, data=request.data, partial=False)  # type: ignore
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class PartialUpdateModelMixin:
    """
    Update a model instance using the 'partial_update' method.

    Source: this mixin is based on the 'UpdateModelMixin' from the 'rest_framework.mixins' module.
    """

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()  # type: ignore
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # type: ignore
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class PermissionByActionMixin:
    action = None
    permission_classes = []
    permission_classes_by_action = {}

    def get_permissions(self):
        """
        Return different permissions for each action if this is defined. Otherwise return default
        'permissions_classes'.

        Example setup:
            permission_classes_by_action = {
                "list": [IsAdminUser],
                "retrieve": [IsOwnerOfUser | IsAdminUser],
                "create": [IsNotMember],
                "update": [IsOwnerOfUser],
                "partial_update": [IsOwnerOfUser],
            }
        """
        assert self.permission_classes_by_action is not None, (
            f"'{self.__class__.__name__}' should include a `permission_classes_by_action` attribute, or don't inherit "
            f"the 'PermissionByActionMixin' class."
        )

        assert self.action is not None, "'self.action' should not be None. Did you inherit the ViewSetMxin?"

        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]


class SerializerByActionMixin:
    """
    Return different serializer class for each action if this is defined. Otherwise return default 'serializer_class'.

    Example setup:
        serializer_class_by_action = {
            "create": UserCreateSerializer,
            "update": UserUpdateSerializer,
            "partial_update": UserUpdateSerializer,
        }
    """

    action = None
    serializer_class = None
    serializer_class_by_action = None

    def get_serializer_class(self):
        assert self.serializer_class_by_action is not None, (
            f"'{self.__class__.__name__}' should include a `serializer_class_by_action` attribute, or don't inherit "
            f"the 'SerializerByActionMixin' class."
        )

        assert self.action is not None, "'self.action' should not be None. Did you inherit the ViewSetMxin?"

        try:
            return self.serializer_class_by_action[self.action]
        except KeyError:
            assert self.serializer_class is not None, (
                f"'{self.__class__.__name__}' should either include a `serializer_class` attribute, or override the "
                "`get_serializer_class()` method."
            )
            return self.serializer_class


class ObjectRoleMixin(viewsets.GenericViewSet):
    """
    Given an object (Workspace, Project, Job, etc.) return the role based on that object.

    In order to determine the role we need: `workspace` or `project`. This allows us to lookup from `Membership` model.
    """

    def get_object_project(self):
        raise NotImplementedError()

    def get_object_workspace(self):
        return self.get_object_project().workspace

    def get_workspace_role(self, user, workspace=None, *args, **kwargs):
        if not workspace:
            workspace = self.get_object_workspace()
        return Membership.get_workspace_role(user, workspace)

    def get_roles_for_project(self, user, project=None, *args, **kwargs):
        if not project:
            project = self.get_object_project()
        return Membership.get_roles_for_project(user, project)

    def get_object_without_permissioncheck(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            f"Expected view '{self.__class__.__name__}' to be called with a URL keyword argument named "
            f"'{lookup_url_kwarg}'. Check your URL conf, or set the '.lookup_field' attribute on the view correctly."
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            return get_object_or_404(queryset, **filter_kwargs)
        except Http404 as exc:
            if hasattr(self, "get_object_fallback"):
                return self.get_object_fallback()  # type: ignore
            raise Http404 from exc

    def get_object_roles(self, request) -> list:
        if not self.detail:
            raise SystemError(
                "This method is only for detail views. Somehow the method is now called for a non-detail view."
            )

        self.current_object = self.get_object_without_permissioncheck()

        try:
            object_roles = self.get_roles_for_project(request.user)
        except NotImplementedError:
            pass
        else:
            return object_roles

        try:
            object_role = self.get_workspace_role(request.user)
        except NotImplementedError as exc:
            raise NotImplementedError("ObjectRoleMixin requires either a workspace or a project") from exc
        else:
            return [object_role]

    def get_parrent_roles(self, request) -> list:
        return []

    def initial(self, request, *args, **kwargs):
        """
        This initial method sets the roles of the user in relation to the request and the request's object.
        """
        request.user_roles = [User.get_role(request)]

        if self.detail:
            object_roles = self.get_object_roles(request)
            request.user_roles += list(set(object_roles) - set(request.user_roles))

        if getattr(self, "get_parrent_roles", None):
            request.user_roles += self.get_parrent_roles(request)

        super().initial(request, *args, **kwargs)
