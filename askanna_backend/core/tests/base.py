# -*- coding: utf-8 -*-
import datetime
import io
import typing
import uuid
import zipfile

from rest_framework import status
from users.models import (
    User,
    UserProfile,
    MSP_WORKSPACE,
    WS_ADMIN,
    WS_MEMBER,
    WS_VIEWER,
)
from workspace.models import Workspace


class BaseUserPopulation:
    def setUp(self):
        super().setUp()
        self.workspace_a = Workspace.objects.create(name="test workspace_a")
        self.workspace_b = Workspace.objects.create(name="test workspace_b")
        self.workspace_c = Workspace.objects.create(name="test workspace_c", visibility="PUBLIC")

        self.users = {
            "anna": User.objects.create(
                username="anna",
                is_staff=True,
                is_superuser=True,
                email="anna@askanna.dev",
            ),
            "admin": User.objects.create(
                username="admin",
                email="admin@askanna.dev",
                password="password-admin",
            ),
            "member": User.objects.create(
                username="member",
                email="member@askanna.dev",
                password="password-member",
            ),
            "non_member": User.objects.create(
                username="non_member",
                email="non_member@askanna.dev",
                password="password-non_member",
            ),
            # the following users take a different role in testing and are not needed for primairy tests
            "admin2": User.objects.create(
                username="admin2",
                email="admin2@askanna.dev",
                password="password-admin2",
            ),
            "member2": User.objects.create(
                username="member2",
                email="member2@askanna.dev",
                password="password-member2",
            ),
            "member_wv": User.objects.create(
                username="member_wv",
                email="member_wv@askanna.dev",
                password="password-member_wv",
            ),
            "admin_inactive": User.objects.create(
                username="admin_inactive",
                email="admin_inactive@askanna.dev",
                password="password-admin_inactive",
            ),
            "member_inactive": User.objects.create(
                username="member_inactive",
                email="member_inactive@askanna.dev",
                password="password-member_inactive",
            ),
        }
        self.members = {
            # anna user never has a profile to simulate askanna admin without
            # an explicit access to workspaces and projects
            "anna": None,
            "admin": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin"],
                role=WS_ADMIN,
                name="name of admin in membership",
                job_title="job_title of admin in membership",
                use_global_profile=False,
            ),
            "member": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member"],
                role=WS_MEMBER,
                name="name of member in membership",
                job_title="job_title of member in membership",
                use_global_profile=False,
            ),
            "non_member": None,
            "admin2": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin2"],
                role=WS_ADMIN,
                name="name of admin2 in membership",
                job_title="job_title of admin2 in membership",
                use_global_profile=False,
            ),
            "member2": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member2"],
                role=WS_MEMBER,
                name="name of member2 in membership",
                job_title="job_title of member2 in membership",
                use_global_profile=False,
            ),
            "member_wv": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member_wv"],
                role=WS_VIEWER,
                name="name of member_wv in membership",
                job_title="job_title of member_wv in membership",
                use_global_profile=True,
            ),
            "admin_inactive": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin_inactive"],
                role=WS_ADMIN,
                name="name of admin_inactive in membership",
                job_title="job_title of admin_inactive in membership",
                use_global_profile=False,
                deleted=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
            ),
            "member_inactive": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member_inactive"],
                role=WS_MEMBER,
                name="name of member_inactive in membership",
                job_title="job_title of member_inactive in membership",
                use_global_profile=False,
                deleted=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
            ),
        }
        self.members_workspace2 = {
            # anna user never has a profile to simulate askanna admin without
            # an explicit access to workspaces and projects
            "anna": None,
            "admin": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_b.uuid,
                user=self.users["admin"],
                role=WS_ADMIN,
                name="name of admin in membership",
                job_title="job_title of admin in membership",
            ),
            "member": None,
            "non_member": None,
            "admin2": None,
            "member2": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_b.uuid,
                user=self.users["member2"],
                role=WS_MEMBER,
                name="name of member2 in membership",
                job_title="job_title of member2 in membership",
            ),
            "member3": None,
            "member_inactive": UserProfile.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_b.uuid,
                user=self.users["member_inactive"],
                role=WS_MEMBER,
                name="name of member_inactive in membership",
                job_title="job_title of member_inactive in membership",
                use_global_profile=False,
                deleted=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
            ),
        }

    def activate_user(self, username):
        if username not in self.users.keys():
            raise ValueError(f"{username} is not part of the test population")

        token = self.users.get(username).auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def tearDown(self):
        """
        Remove all the user instances we had setup for the test
        """
        super().tearDown()
        for _, user in self.users.items():
            user.delete()


class BaseUploadTestMixin:
    def do_create_entry(self, create_url, filename, filesize):

        payload = {
            "filename": filename,
            "project": self.jobruns["run1"].jobdef.project.short_uuid,  # project is only needed in package upload
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
        parent_object = self.do_create_entry(create_url, filename=fileobjectname, filesize=file_size)
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
            try:
                self.assertEqual(chunk_upload_req.status_code, status.HTTP_200_OK)
            except AssertionError as e:
                raise AssertionError(e)

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
