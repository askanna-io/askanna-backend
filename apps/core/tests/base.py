import datetime

from account.models.membership import MSP_WORKSPACE, Membership
from account.models.user import User
from core.permissions.roles import WorkspaceAdmin, WorkspaceMember, WorkspaceViewer
from project.models import Project
from workspace.models import Workspace


class BaseUserPopulation:
    def setUp(self):
        super().setUp()
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
                role=WorkspaceMember.code,
                name="name of member in membership",
                job_title="job_title of member in membership",
                use_global_profile=False,
            ),
            "non_member": None,
            "admin2": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin2"],
                role=WorkspaceAdmin.code,
                name="name of admin2 in membership",
                job_title="job_title of admin2 in membership",
                use_global_profile=False,
            ),
            "member2": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member2"],
                role=WorkspaceMember.code,
                name="name of member2 in membership",
                job_title="job_title of member2 in membership",
                use_global_profile=False,
            ),
            "member_wv": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member_wv"],
                role=WorkspaceViewer.code,
                name="name of member_wv in membership",
                job_title="job_title of member_wv in membership",
                use_global_profile=True,
            ),
            "admin_inactive": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["admin_inactive"],
                role=WorkspaceAdmin.code,
                name="name of admin_inactive in membership",
                job_title="job_title of admin_inactive in membership",
                use_global_profile=False,
                deleted_at=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC),
            ),
            "member_inactive": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_a.uuid,
                user=self.users["member_inactive"],
                role=WorkspaceMember.code,
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
                role=WorkspaceAdmin.code,
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
                role=WorkspaceMember.code,
                name="name of member2 in membership",
                job_title="job_title of member2 in membership",
                use_global_profile=True,
            ),
            "member3": None,
            "member_inactive": Membership.objects.create(
                object_type=MSP_WORKSPACE,
                object_uuid=self.workspace_b.uuid,
                user=self.users["member_inactive"],
                role=WorkspaceMember.code,
                name="name of member_inactive in membership",
                job_title="job_title of member_inactive in membership",
                use_global_profile=False,
                deleted_at=datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC),
            ),
        }

    def activate_user(self, username):
        if username not in self.users.keys():
            raise ValueError(f"{username} is not part of the test population")

        token = self.users.get(username).auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def tearDown(self):
        super().tearDown()
        for user in self.users.values():
            user.delete()

        for project in self.projects.values():
            project.delete()

        for workspace in self.workspaces.values():
            workspace.delete()
