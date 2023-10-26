from pathlib import Path

import sentry_sdk
from django.http import FileResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.http import RangeFileResponse
from core.permissions import AskAnnaPermission
from core.viewsets import AskAnnaGenericViewSet
from storage.models import File
from storage.serializers import FileInfoSerializer


def _validate_file_exists(instance: File) -> bool:
    """
    Validate that the file exists in the storage. If not, log an error in Sentry and return False.

    Args:
        instance (File): A file instance

    Returns:
        bool: True if the file exists, False otherwise
    """
    if instance.file.storage.exists(instance.file.name) is False:
        sentry_sdk.set_context(
            "file info",
            {
                "file_suuid": instance.suuid,
                "file_storage": instance.file.storage,
                "file_name": instance.file.name,
            },
        )
        sentry_sdk.capture_exception(Exception("File not found in Storage while it's active in the File database"))
        return False

    return True


class FileViewSet(AskAnnaGenericViewSet):
    queryset = File.objects.active(add_select_related=True)  # type: ignore
    lookup_field = "suuid"

    permission_classes = [AskAnnaPermission]

    @extend_schema(
        summary="Get info about a file",
        description=(
            "Get information about a file, including the download URL. The information for downloading the file "
            "contains the type of service used and the URL to download the file. The type can be used to determine "
            "which features are available to download the file."
        ),
        responses={
            200: FileInfoSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="File not found or no permission to access"),
        },
    )
    @action(
        detail=True,
        methods=["get"],
        serializer_class=FileInfoSerializer,
    )
    def info(self, request, *args, **kwargs):
        instance = self.get_object()

        if _validate_file_exists(instance) is False:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Download a file",
        description=(
            "Download a file. The response contains the file content. The response header contain the file name and "
            "content type.<br><br>"
            "Supported request headers:<br>"
            "<ol>"
            "<li><b>Range</b> - The value of this header is used to download a partial content of the file. Supported "
            "values:"
            "<ul>"
            "  <li>bytes=0-100</li>"
            "  <li>bytes=100- (start at byte 100 till the end of the file)</li>"
            "  <li>bytes=-100 (get the last 100 bytes)</li>"
            "</ul>"
            "</li>"
            "<li><b>Response-Content-Disposition</b> - The value of this header is used to set the "
            "Content-Disposition of the response. If the value contains a filename, then this filename is used. The "
            "HTTP context is either 'attachment' or 'inline'. Supported values:"
            "<ul>"
            '  <li>attachment; filename="filename.txt"</li>'
            "  <li>attachment</li>"
            '  <li>filename="filename.txt"</li>'
            "</ul>"
            "</li>"
            "</ol>"
        ),
        responses={
            200: OpenApiResponse(description="Content of a file (binary string)"),
            206: OpenApiResponse(description="Partial content of a file (binary string)"),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="File not found or no permission to access"),
            416: OpenApiResponse(description="Invalid range request"),
        },
    )
    @action(detail=True, methods=["get"])
    def download(self, request, *args, **kwargs):
        instance = self.get_object()

        if _validate_file_exists(instance) is False:
            return Response(status=status.HTTP_404_NOT_FOUND)

        file_object = instance.file.file
        filename = Path(file_object.name).name
        content_type = file_object.content_type
        as_attachment = True

        if "HTTP_RESPONSE_CONTENT_DISPOSITION" in request.META:
            response_content_disposition = request.META["HTTP_RESPONSE_CONTENT_DISPOSITION"].split(";")

            as_attachment = response_content_disposition[0] == "attachment"

            if len(response_content_disposition) > 1 and response_content_disposition[1].strip().startswith(
                "filename="
            ):
                filename = response_content_disposition[1].split("=")[1]
                filename = filename[1:-1] if filename.startswith('"') else filename

        if "HTTP_RANGE" in request.META:
            response = RangeFileResponse(
                file_object,
                request.META["HTTP_RANGE"],
                filename=filename,
                content_type=content_type,
            )

            if response.status_code == status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE:
                response = Response(status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
        else:
            response = FileResponse(
                file_object,
                as_attachment=as_attachment,
                filename=filename,
                content_type=content_type,
            )
            response["Accept-Ranges"] = "bytes"

        return response
