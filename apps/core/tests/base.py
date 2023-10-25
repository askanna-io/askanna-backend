import datetime
import io
import uuid
import zipfile
from collections.abc import Callable

from rest_framework import status

from account.models.membership import (
    MSP_WORKSPACE,
    WS_ADMIN,
    WS_MEMBER,
    WS_VIEWER,
    Membership,
)
from account.models.user import User
from project.models import Project
from workspace.models import Workspace


class BaseUserPopulation:
    def setUp(self):
        super().setUp()  # type: ignore
        self.users = {
            "anna": User.objects.create(
                username="anna",
                is_staff=True,
                is_superuser=True,
                email="anna@askanna.dev",
            ),
            "admin": User.objects.create(  # nosec: B106
                username="admin",
                email="admin@askanna.dev",
                password="password-admin",
            ),
            "member": User.objects.create(  # nosec: B106
                username="member",
                name="member",
                job_title="job title for member",
                email="member@askanna.dev",
                password="password-member",
            ),
            "non_member": User.objects.create(  # nosec: B106
                username="non_member",
                email="non_member@askanna.dev",
                password="password-non_member",
            ),
            # the following users take a different role in testing and are not needed for primairy tests
            "admin2": User.objects.create(  # nosec: B106
                username="admin2",
                email="admin2@askanna.dev",
                password="password-admin2",
            ),
            "member2": User.objects.create(  # nosec: B106
                username="member2",
                name="member2",
                job_title="job title for member2",
                email="member2@askanna.dev",
                password="password-member2",
            ),
            "member_wv": User.objects.create(  # nosec: B106
                username="member_wv",
                email="member_wv@askanna.dev",
                password="password-member_wv",
            ),
            "admin_inactive": User.objects.create(  # nosec: B106
                username="admin_inactive",
                email="admin_inactive@askanna.dev",
                password="password-admin_inactive",
            ),
            "member_inactive": User.objects.create(  # nosec: B106
                username="member_inactive",
                email="member_inactive@askanna.dev",
                password="password-member_inactive",
            ),
            "admin_for_workspace_b": User.objects.create(  # nosec: B106
                username="admin_for_workspace_b",
                email="admin_b@askanna.dev",
            ),
            "admin_for_workspace_c": User.objects.create(  # nosec: B106
                username="admin_for_workspace_c",
                email="admin_c@askanna.dev",
            ),
        }

        self.workspace_a = Workspace.objects.create(
            name="test workspace_a",
            created_by_user=self.users["admin"],
        )
        self.workspace_b = Workspace.objects.create(
            name="test workspace_b",
            created_by_user=self.users["admin_for_workspace_b"],
        )
        self.workspace_c = Workspace.objects.create(
            name="test workspace_c",
            created_by_user=self.users["admin_for_workspace_c"],
            visibility="PUBLIC",
        )
        self.workspaces = {
            "workspace_a": self.workspace_a,
            "workspace_b": self.workspace_b,
            "workspace_c": self.workspace_c,
        }

        self.projects = {
            "project_a_wp_private_pr_private": Project.objects.create(
                name="test project_a_1",
                workspace=self.workspace_a,
            ),
            "project_a_wp_private_pr_public": Project.objects.create(
                name="test project_a_2",
                workspace=self.workspace_a,
                visibility="PUBLIC",
            ),
            "project_b_wp_private_pr_private": Project.objects.create(
                name="test project_b_1",
                workspace=self.workspace_b,
            ),
            "project_c_wp_public_pr_private": Project.objects.create(
                name="test project_c_1",
                workspace=self.workspace_c,
            ),
            "project_c_wp_public_pr_public": Project.objects.create(
                name="test project_c_2",
                workspace=self.workspace_c,
                visibility="PUBLIC",
            ),
        }

        self.members = {
            "anna": None,
            "admin": Membership.objects.get(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin"],
            ),
            "member": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member"],
                role=WS_MEMBER,
                name="name of member in membership",
                job_title="job_title of member in membership",
                use_global_profile=False,
            ),
            "non_member": None,
            "admin2": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin2"],
                role=WS_ADMIN,
                name="name of admin2 in membership",
                job_title="job_title of admin2 in membership",
                use_global_profile=False,
            ),
            "member2": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member2"],
                role=WS_MEMBER,
                name="name of member2 in membership",
                job_title="job_title of member2 in membership",
                use_global_profile=False,
            ),
            "member_wv": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member_wv"],
                role=WS_VIEWER,
                name="name of member_wv in membership",
                job_title="job_title of member_wv in membership",
                use_global_profile=True,
            ),
            "admin_inactive": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin_inactive"],
                role=WS_ADMIN,
                name="name of admin_inactive in membership",
                job_title="job_title of admin_inactive in membership",
                use_global_profile=False,
                deleted_at=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC),
            ),
            "member_inactive": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member_inactive"],
                role=WS_MEMBER,
                name="name of member_inactive in membership",
                job_title="job_title of member_inactive in membership",
                use_global_profile=False,
                deleted_at=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC),
            ),
        }
        self.members_workspace2 = {
            # anna user never has a profile to simulate askanna admin without
            # an explicit access to workspaces and projects
            "anna": None,
            "admin": Membership.objects.create(
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
            "member2": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_b.uuid,
                user=self.users["member2"],
                role=WS_MEMBER,
                name="name of member2 in membership",
                job_title="job_title of member2 in membership",
                use_global_profile=True,
            ),
            "member3": None,
            "member_inactive": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_b.uuid,
                user=self.users["member_inactive"],
                role=WS_MEMBER,
                name="name of member_inactive in membership",
                job_title="job_title of member_inactive in membership",
                use_global_profile=False,
                deleted_at=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC),
            ),
        }

    def activate_user(self, username):
        if username not in self.users.keys():
            raise ValueError(f"{username} is not part of the test population")

        token = self.users.get(username).auth_token  # type: ignore
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

    def tearDown(self):
        super().tearDown()  # type: ignore
        for user in self.users.values():
            user.delete()

        for project in self.projects.values():
            project.delete()

        for workspace in self.workspaces.values():
            workspace.delete()


class BaseUploadTestMixin:
    def do_create_entry(self, create_url, filename, filesize):
        payload = {
            "filename": filename,
            "project_suuid": self.runs["run1"].jobdef.project.suuid,  # type: ignore
            "size": filesize,
        }

        response = self.client.post(  # type: ignore
            create_url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, AssertionError(response.status_code)

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
        file_buffer.seek(0)
        return file_buffer, file_size

    def do_file_upload(
        self,
        create_url: str | None = None,
        create_chunk_url: Callable[[dict], str] | None = None,
        upload_chunk_url: Callable[[dict, str], str] | None = None,
        finish_upload_url: Callable[[dict], str] | None = None,
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

            if not create_chunk_url:
                raise ValueError("create_chunk_url is not set")

            req_chunk = self.client.post(  # type: ignore
                create_chunk_url(parent_object),
                config,
                format="json",
            )
            assert req_chunk.status_code == status.HTTP_201_CREATED

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

            if not upload_chunk_url:
                raise ValueError("upload_chunk_url is not set")

            chunk_upload_req = self.client.post(  # type: ignore
                upload_chunk_url(parent_object, chunk_uuid),
                chunkinfo,
                format="multipart",
            )
            assert chunk_upload_req.status_code == status.HTTP_200_OK

        # finish upload
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

        if not finish_upload_url:
            raise ValueError("finish_upload_url is not set")

        final_upload_req = self.client.post(  # type: ignore
            finish_upload_url(parent_object),
            data=final_call_payload,
        )
        assert final_upload_req.status_code == status.HTTP_200_OK
