# -*- coding: utf-8 -*-
import io
import typing
import uuid
import zipfile

from rest_framework import status


class BaseUploadTestMixin:
    def do_create_entry(self, create_url, filename, filesize):

        payload = {
            "filename": filename,
            "project": self.jobruns["run1"].jobdef.project.short_uuid,
            "size": filesize,
        }

        response = self.client.post(
            create_url,
            payload,
            format="json",
            HTTP_HOST="testserver",
        )
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        except AssertionError as e:
            raise AssertionError(e)
        return response.data.copy()

    def create_file_object(self, filename):

        file_buffer = io.BytesIO()
        file_buffer.name = filename
        with zipfile.ZipFile(file_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name, data in [
                ("1.txt", io.BytesIO(b"111")),
                ("2.txt", io.BytesIO(b"222")),
            ]:
                zip_file.writestr(file_name, data.getvalue())
        file_size = len(file_buffer.getvalue())
        # reset pointer as it was never opened
        file_buffer.seek(0)
        return file_buffer, file_size

    def do_file_upload(
        self,
        create_url: str = None,
        create_chunk_url: typing.Callable[[dict], str] = None,
        upload_chunk_url: typing.Callable[[dict, str], str] = None,
        finish_upload_url: typing.Callable[[dict], str] = None,
        fileobjectname: str = "testartifact.zip",
    ):
        file_buffer, file_size = self.create_file_object(filename=fileobjectname)
        parent_object = self.do_create_entry(
            create_url, filename=fileobjectname, filesize=file_size
        )
        resumable_identifier = str(uuid.uuid4())

        # register new chunks (1)
        number_of_chunks = 1
        for chunk_nr in range(0, number_of_chunks):
            config = {
                "filename": "",
                "size": 0,
                "file_no": 0,
                "is_last": False,
            }
            config.update(
                **{
                    "filename": chunk_nr + 1,
                    "size": file_size,
                    "file_no": chunk_nr + 1,
                    "is_last": chunk_nr + 1 == number_of_chunks,
                }
            )
            req_chunk = self.client.post(
                create_chunk_url(parent_object),
                config,
                format="json",
            )
            self.assertEqual(req_chunk.status_code, status.HTTP_201_CREATED)
            chunk_uuid = req_chunk.data.get("uuid")

            chunkinfo = {
                "resumableChunkSize": file_size,
                "resumableTotalSize": file_size,
                "resumableType": "application/zip",
                "resumableIdentifier": resumable_identifier,
                "resumableFilename": fileobjectname,
                "resumableRelativePath": fileobjectname,
                "resumableTotalChunks": number_of_chunks,
                "resumableChunkNumber": chunk_nr + 1,
                "resumableCurrentChunkSize": 1,
            }
            chunkinfo.update(**{"file": file_buffer})
            chunk_upload_req = self.client.post(
                upload_chunk_url(parent_object, chunk_uuid),
                chunkinfo,
                format="multipart",
            )
            print(chunk_upload_req.content, chunk_upload_req.status_code)
            try:
                self.assertEqual(chunk_upload_req.status_code, status.HTTP_200_OK)
            except AssertionError as e:
                raise AssertionError(e)
            # self.assertTrue(False)

        # finish uplaod
        final_call_payload = {
            "resumableChunkSize": file_size,
            "resumableTotalSize": file_size,
            "resumableType": "application/zip",
            "resumableIdentifier": resumable_identifier,
            "resumableFilename": fileobjectname,
            "resumableRelativePath": fileobjectname,
            "resumableTotalChunks": number_of_chunks,
            "resumableChunkNumber": 1,
            "resumableCurrentChunkSize": 1,
        }
        final_upload_req = self.client.post(
            finish_upload_url(parent_object),
            data=final_call_payload,
        )
        self.assertEqual(final_upload_req.status_code, status.HTTP_200_OK)
