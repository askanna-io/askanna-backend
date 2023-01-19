import django
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from resumable.files import ResumableFile


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404 if the filter_kwargs don't match the required
    types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError, ValidationError):
        raise Http404


class BaseChunkedPartViewSet(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Request an uuid to upload a chunk
    """

    filter_backends = []

    def get_upload_dir(self, chunkpart):
        return settings.UPLOAD_ROOT

    def check_existence(self, request, chunkpart, **kwargs):
        """
        We check the existence of a potential chunk to be uploaded.
        This prevents a new POST action from the client and we don't
        have to process this (saves time)
        """
        storage_location = FileSystemStorage(location=self.get_upload_dir(chunkpart))

        r = ResumableFile(storage_location, request.GET)
        # default response
        response = Response({"message": "chunk upload needed"}, status=404)
        if r.chunk_exists:
            response = Response({"message": "chunk already exists"}, status=200)
        response["Cache-Control"] = "no-cache"
        return response

    @action(detail=True, methods=["post"])
    def chunk(self, request, **kwargs):
        """
        Receive one chunk via a POST request
        """
        chunkpart = self.get_object()

        if request.method == "GET":
            return self.check_existence(request, chunkpart, **kwargs)
        chunk: django.core.files.uploadedfile.InMemoryUploadedFile = request.FILES.get("file")
        storage_location = FileSystemStorage(location=self.get_upload_dir(chunkpart))

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


class BaseUploadFinishViewSet:
    upload_target_location = ""
    upload_finished_signal = None
    upload_finished_message = "upload completed"

    def get_upload_dir(self, obj):
        return settings.UPLOAD_ROOT

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        pass

    def get_upload_target_location(self, request, obj, **kwargs):
        return self.upload_target_location

    def store_as_filename(self, resumable_filename, obj):
        return resumable_filename

    @action(detail=True, methods=["post"])
    def finish_upload(self, request, **kwargs):
        """Register that the upload of all chunks is finished"""
        obj = self.get_object()

        storage_location = FileSystemStorage(location=self.get_upload_dir(obj))
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
