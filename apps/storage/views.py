from pathlib import Path

import sentry_sdk
from django.core.cache import cache
from django.http import FileResponse
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from core.http import RangeFileResponse
from core.permissions import AskAnnaPermissionByAction
from core.viewsets import AskAnnaGenericViewSet
from storage.models import File
from storage.serializers import (
    FileInfoSerializer,
    FileUploadCompleteSerializer,
    FileUploadPartSerializer,
)
from storage.utils.file import get_content_type_from_file
from storage.utils.image import filename_for_resized_image, resize_image


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
    queryset = File.objects.active(add_select_related=True)
    serializer_class = FileInfoSerializer
    permission_classes = [AskAnnaPermissionByAction]
    parser_classes = [MultiPartParser, JSONParser]

    @extend_schema(summary="Get info about a file")
    @action(detail=True, methods=["get"])
    def info(self, request, *args, **kwargs):
        """
        Get information about a file, including the download URL. The information for downloading the file contains
        the type of service used and the URL to download the file. The type can be used to determine which features
        are available to download the file.
        """
        instance = self.get_object()

        if instance.completed_at is None:
            return Response(
                {
                    "detail": "File upload is not completed. It is not possible to download a file that is not "
                    "completed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if _validate_file_exists(instance) is False:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Download a file",
        description=(
            "Download a file. The response contains the file content. The response header contain the file name and "
            "content type.<br><br>"
            "When the file is an image, you can resize the image by setting the width parameter. It will return a "
            "version of the image given the requested width."
        ),
        parameters=[
            OpenApiParameter(
                name="file_path",
                type=str,
                location=OpenApiParameter.QUERY,
                description=(
                    "When the file_path is set and the file is a zip file, then the file requested by file_path is "
                    "extracted and send as the response content or i.c.w. the Range header a specific range from the "
                    "file."
                ),
            ),
            OpenApiParameter(
                name="width",
                type=int,
                location=OpenApiParameter.QUERY,
                description=(
                    "Only for image files with the purpose of creating avatar files that are smaller and square. The "
                    "width is used to resize the image to the number of pixels set by the width parameter. The height "
                    "is set to the same value as the width."
                ),
            ),
            OpenApiParameter(
                name="Range",
                type=str,
                location=OpenApiParameter.HEADER,
                description=(
                    "Add the Range header to download a range from the file. Supported values:"
                    "<ul>"
                    "  <li>bytes=0-100</li>"
                    "  <li>bytes=100- (start at byte 100 till the end of the file)</li>"
                    "  <li>bytes=-100 (get the last 100 bytes)</li>"
                    "</ul>"
                    "</li>"
                ),
            ),
            OpenApiParameter(
                name="Response-Content-Disposition",
                type=str,
                location=OpenApiParameter.HEADER,
                description=(
                    "Set the Content-Disposition of the response. If the value contains a filename, then this "
                    "filename is used. The HTTP context is either 'attachment' or 'inline'. Supported values:"
                    "<ul>"
                    '  <li>attachment; filename="filename.txt"</li>'
                    "  <li>attachment</li>"
                    '  <li>filename="filename.txt"</li>'
                    "</ul>"
                    "</li>"
                    "</ol>"
                ),
            ),
        ],
        responses={
            200: OpenApiResponse(description="Content of a file (binary string)"),
            206: OpenApiResponse(description="Partial content of a file (binary string)"),
        },
    )
    @action(detail=True, methods=["get"])
    def download(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.completed_at is None:
            return Response(
                {
                    "detail": "File upload is not completed. It is not possible to download a file that is not "
                    "completed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if _validate_file_exists(instance) is False:
            return Response(status=status.HTTP_404_NOT_FOUND)

        file_path = request.query_params.get("file_path")
        if file_path:
            file_path = file_path.strip('"')

            if not instance.is_zipfile:
                return Response(
                    {
                        "detail": (
                            "The file_path parameter is only supported for zip files and the requested file is not "
                            "a zip file."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                file_object = instance.get_file_from_zipfile(file_path)
            except FileNotFoundError:
                return Response(
                    {"detail": f"File path '{file_path}' not found in this zip file."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            filename = Path(file_path).name
            content_type = get_content_type_from_file(file_object)
        else:
            file_object = instance.file.file
            filename = instance.name or Path(file_object.name).name
            content_type = instance.content_type or file_object.content_type

        as_attachment = True
        if "HTTP_RESPONSE_CONTENT_DISPOSITION" in request.META:
            response_content_disposition = request.META["HTTP_RESPONSE_CONTENT_DISPOSITION"].split(";")

            as_attachment = response_content_disposition[0] == "attachment"

            if len(response_content_disposition) > 1 and response_content_disposition[1].strip().startswith(
                "filename="
            ):
                filename = response_content_disposition[1].split("=")[1]
                filename = filename[1:-1] if filename.startswith('"') else filename

        width = request.query_params.get("width")
        if width:
            if "HTTP_RANGE" in request.META:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "Range header not supported in combination with the width parameter"},
                )

            try:
                width = int(width)
            except ValueError:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "Width parameter must be an integer"},
                )

            if width <= 0:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "Width parameter must be greater than 0"},
                )

            if width > 1000:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "Width parameter must be less than 1000"},
                )

            if content_type.startswith("image/") is False:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "Width parameter is only supported for image files"},
                )

            if "HTTP_RESPONSE_CONTENT_DISPOSITION" not in request.META or (
                "HTTP_RESPONSE_CONTENT_DISPOSITION" in request.META
                and "filename=" not in request.META["HTTP_RESPONSE_CONTENT_DISPOSITION"]
            ):
                filename = filename_for_resized_image(filename, width)

            return FileResponse(
                cache.get_or_set(
                    f"image_{instance.suuid}_{width}",
                    lambda: resize_image(file_object, width),
                    timeout=60 * 60 * 4,  # 4 hours
                ),
                as_attachment=as_attachment,
                filename=filename,
                content_type=content_type,
            )

        if "HTTP_RANGE" in request.META:
            response = RangeFileResponse(
                file_object,
                request.META["HTTP_RANGE"],
                filename=filename,
                content_type=content_type,
            )

            if response.status_code == status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE:
                return Response(status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
        else:
            response = FileResponse(
                file_object,
                as_attachment=as_attachment,
                filename=filename,
                content_type=content_type,
            )

        response["Accept-Ranges"] = "bytes"
        response["X-Frame-Options"] = "SAMEORIGIN"

        return response

    @extend_schema(summary="Upload part of a file")
    @action(detail=True, methods=["put"], url_path="upload/part", serializer_class=FileUploadPartSerializer)
    def upload_part(self, request, *args, **kwargs):
        """
        Upload a part of a file by doing a request with the part number and the content of the part. Optionally
        you can add the ETag of the part. If you submit the ETag, it will be used to validate the sended part.

        The response contains the part number and ETag of the part. The information can be used in the final request to
        complete the upload.
        """
        instance = self.get_object()

        if instance.completed_at:
            return Response(
                {"detail": "File upload is already completed and uploading new parts is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save_part()

        return Response(serializer.data)

    @extend_schema(
        summary="Complete an upload",
        responses={
            200: OpenApiResponse(
                description=(
                    "Upload completed and the file is stored in the storage. The response contains information about "
                    "the file."
                ),
                response=FileInfoSerializer,
            ),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="upload/complete",
        serializer_class=FileUploadCompleteSerializer,
    )
    def upload_complete(self, request, *args, **kwargs):
        """
        Do a request to complete an upload. This will merge all uploaded parts into one file and store it in the
        storage. The uploaded parts will be deleted after the merge is completed.

        Before the upload is completed, the uploaded file is validated. For validation you can submit the ETag and an
        array listing all parts that are uploaded. For each part you need to submit the part number and optionally the
        ETag. This information was provided via the response after uploading the part.
        """
        instance = self.get_object()

        if instance.completed_at:
            return Response(
                {"detail": "File upload is already completed and uploading new parts is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Block the file from being processed by f.e. a second complete upload request.
        if cache.get(f"storage.File:{instance.suuid}:lock", default=False) is True:
            return Response(
                {"detail": "File is locked by another process and upload cannot be completed at this moment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.set(f"storage.File:{instance.suuid}:lock", True)

        if not instance.part_filenames:
            return Response(
                {"detail": "No uploaded parts found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.complete_upload()

        instance.refresh_from_db()
        serializer_after_complete = FileInfoSerializer(instance, context=self.get_serializer_context())

        return Response(serializer_after_complete.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Abort an upload",
        responses={
            204: OpenApiResponse(description="Upload aborted and all uploaded parts are deleted"),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="upload/abort",
    )
    def upload_abort(self, request, *args, **kwargs):
        """
        Do a request to abort an upload. All uploaded parts will be deleted and the object the uploaded was created
        for might be deleted as well. The latter is depending on the related object configuration.

        Abort an upload is only possible when the upload is not completed yet.
        """
        instance = self.get_object()

        if instance.completed_at:
            return Response(
                {"detail": "Upload is already completed. It is not possible to abort an upload that is completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Block the file from being processed by f.e. a second abort upload request.
        locked = cache.get(f"storage.File:{instance.suuid}:lock", default=False)
        if locked is True:
            return Response(
                {"detail": "File is locked by another process and upload cannot be aborted at this moment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.set(f"storage.File:{instance.suuid}:lock", True)

        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
