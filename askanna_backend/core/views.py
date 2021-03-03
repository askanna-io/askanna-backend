from django.core.files.storage import FileSystemStorage
from django.conf import settings

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_extensions.mixins import NestedViewSetMixin

from resumable.files import ResumableFile

from core.mixins import HybridUUIDMixin


class BaseChunkedPartViewSet(
    HybridUUIDMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """

    """

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
        chunk = request.FILES.get("file")
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

        return Response(
            {"uuid": str(chunkpart.uuid), "message": "chunk stored"}, status=200
        )


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
        target_location = FileSystemStorage(
            location=self.get_upload_target_location(request=request, obj=obj)
        )
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
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]
