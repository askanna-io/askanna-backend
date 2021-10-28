import django
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from resumable.files import ResumableFile

from typing import Optional, Union

from core.permissions import (
    BaseRoleType,
    ProjectAdmin,
    ProjectMember,
    ProjectNoMember,
    WorkspaceAdmin,
    WorkspaceMember,
)
from users.models import Membership, User


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404
    if the filter_kwargs don't match the required types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError, ValidationError):
        raise Http404


class BaseChunkedPartViewSet(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """"""

    def check_existence(self, request, **kwargs):
        """
        We check the existence of a potential chunk to be uploaded.
        This prevents a new POST action from the client and we don't
        have to process this (saves time)
        """
        storage_location = FileSystemStorage(location=settings.UPLOAD_ROOT)

        r = ResumableFile(storage_location, request.GET)
        # default response
        response = Response({"message": "chunk upload needed"}, status=404)
        if r.chunk_exists:
            response = Response({"message": "chunk already exists"}, status=200)
        response["Cache-Control"] = "no-cache"
        return response

    @action(detail=True, methods=["post", "get"])
    def chunk(self, request, **kwargs):
        """
        Receives one chunk in the POST request

        """
        chunkpart = self.get_object()

        if request.method == "GET":
            return self.check_existence(request, **kwargs)
        chunk: django.core.files.uploadedfile.InMemoryUploadedFile = request.FILES.get("file")
        storage_location = FileSystemStorage(location=settings.UPLOAD_ROOT)

        r = ResumableFile(storage_location, request.POST)
        if r.chunk_exists:
            return Response({"message": "chunk already exists"}, status=200)
        r.process_chunk(chunk)

        chunkpart.filename = "%s%s%s" % (
            r.filename,
            r.chunk_suffix,
            r.kwargs.get("resumableChunkNumber").zfill(4),
        )
        chunkpart.save()

        return Response({"uuid": str(chunkpart.uuid), "message": "chunk stored"}, status=200)


class BaseUploadFinishMixin:
    upload_target_location = ""
    upload_finished_signal = None
    upload_finished_message = "upload completed"

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        pass

    def get_upload_target_location(self, request, obj, **kwargs):
        return self.upload_target_location

    def store_as_filename(self, resumable_filename, obj):
        return resumable_filename

    @action(detail=True, methods=["post"])
    def finish_upload(self, request, **kwargs):
        obj = self.get_object()

        storage_location = FileSystemStorage(location=settings.UPLOAD_ROOT)
        target_location = FileSystemStorage(location=self.get_upload_target_location(request=request, obj=obj))
        r = ResumableFile(storage_location, request.POST)
        if r.is_complete:
            target_location.save(self.store_as_filename(r.filename, obj), r)
            self.post_finish_upload_update_instance(request, obj, r)
            r.delete_chunks()

            if self.upload_finished_signal:
                self.upload_finished_signal.send(
                    sender=self.__class__,
                    postheaders=dict(request.POST.lists()),
                    obj=obj,
                )

        response = Response({"message": self.upload_finished_message}, status=200)
        response["Cache-Control"] = "no-cache"
        return response


class SerializerByActionMixin:
    def get_serializer_class(self):
        """
        Return different serializer class for each http method

        Example setup:
        serializer_classes_by_action = {
            "post": UserCreateSerializer,
            "put": UserUpdateSerializer,
            "patch": UserUpdateSerializer,
        }
        """
        actions = self.serializer_classes_by_action
        action_method = self.request.method.lower()

        serializer = actions.get(action_method)
        if not serializer:
            # return default serializer in case we don't find a specified one for method specific
            return self.serializer_class
        return serializer


class PermissionByActionMixin:
    def get_permissions(self):
        """
        Return different permissions for each action if this is defined
        otherwise return default `permissions_classes`
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


def workspace_to_project_role(workspace_role):
    """
    Maps a workspace role to a more specific Project role (automatic role inheritance)
    """
    mapping = {
        WorkspaceAdmin: ProjectAdmin,
        WorkspaceMember: ProjectMember,
    }

    return mapping.get(workspace_role, None)


class ObjectRoleMixin:
    """
    Given an object (Workspace,Project,Job,Run,Artifact,Result,Log)
    Return the role based on that object.
    In order to determine the Role we need: `workspace` or `project`.
    This allows us to lookup from `Membership` model on: WS/PR

    There is an automatic translation of workspace roles into project roles
    May there a project role be explicit assigned (e.g. project member PM) and
    on workspace level the user is a workspace admin (WA) the user would be assigned:
    - WA + PA
    - PM (from project membership itself)

    The resulting and effective roles will be:
    - WA + PA

    We take the "strongest" role in each layer. In this case on the project layer
    the user got an PA inherited by WA and then the PM is neglected.
    """

    base_role = ProjectNoMember

    def get_object_workspace(self):
        raise NotImplementedError()

    def get_object_project(self):
        raise NotImplementedError()

    def get_object_without_permissioncheck(self):
        queryset = self.filter_queryset(self.get_queryset())
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            obj = get_object_or_404(queryset, **filter_kwargs)
        except Http404 as e:
            # not found, do we have a routine for creating a new one in case or fallback?
            if hasattr(self, "get_object_fallback"):
                obj = self.get_object_fallback()
            else:
                raise e
        return obj

    def get_object_role(self, request, *args, **kwargs) -> Union[BaseRoleType, Optional[Membership]]:
        """
        To be executed before super().initial() in our custom initial
        Warning: do not use `self.get_object` as this triggers a permissions check
        before we have the role set.
        Use our own `get_object_without_permissioncheck` to get the object
        """
        object_role = None
        request.membership = None
        self.current_object = None
        if self.detail:
            self.current_object = self.get_object_without_permissioncheck()
            object_role, request.membership = Membership.get_project_role(request.user, self.get_object_project())
            return object_role
        return self.base_role

    def get_list_role(self, request, *args, **kwargs) -> Union[BaseRoleType, Optional[Membership]]:
        ...

    def get_create_role(self, request, *args, **kwargs) -> Union[BaseRoleType, Optional[Membership]]:
        ...

    def get_workspace_role(self, user, *args, **kwargs) -> Union[BaseRoleType, Optional[Membership]]:

        return Membership.get_workspace_role(user, self.get_object_workspace())

    def initial(self, request, *args, **kwargs):
        """
        Here we do a pre-initial call which sets the role of the user
        This was not possible in the standard Django middleware as DRF overwrites this with their own flow
        """
        # set the role and user_roles
        request.role = User.get_role(request)
        request.user_roles = [request.role]

        # we first check for detailview (expeciting these to be the mayority of the views)
        if self.detail and hasattr(self, "get_object_role"):
            # we are in detail view
            object_role = self.get_object_role(request, *args, **kwargs)
            request.user_roles += Membership.get_roles_for_project(request.user, self.get_object_project())
            if object_role:
                request.user_roles.append(object_role)
                request.object_role = object_role

                # additionally retrieve the workspace role for this user
                workspace_role, request.membership = self.get_workspace_role(request.user, *args, **kwargs)
                request.user_roles.append(workspace_role)

                # on top of this, add the "free" roles that comes with the workspace role
                # check whether we should override the original object_role to upgrade based
                # workspace role
                if workspace_to_project_role(workspace_role) is not None:
                    inherited_role = workspace_to_project_role(workspace_role)
                    request.user_roles.append(inherited_role)

                    if inherited_role.prio < object_role.prio:
                        # the new project role should be more important than initial found role
                        # e.g. WorkspaceAdmin = ProjectAdmin
                        # and object_role is ProjectMember
                        # in that case we assign the inherited role towards the request.object_role
                        request.object_role = inherited_role

            elif object_role is None:
                # project membership was not found, try finding the role on Workspace level
                workspace_role, request.membership = self.get_workspace_role(request.user, *args, **kwargs)
                request.user_roles.append(workspace_role)
                request.object_role = workspace_role

                # try setting a project role based on workspace role
                if workspace_to_project_role(workspace_role) is not None:
                    inherited_role = workspace_to_project_role(workspace_role)
                    request.user_roles.append(inherited_role)

        elif self.action == "list" and hasattr(self, "get_list_role"):
            list_role, request.membership = self.get_list_role(request, *args, **kwargs)
            request.user_roles.append(list_role)
        elif self.action == "create" and hasattr(self, "get_create_role"):
            create_role, request.membership = self.get_create_role(request, *args, **kwargs)
            request.user_roles.append(create_role)

        super().initial(request, *args, **kwargs)
