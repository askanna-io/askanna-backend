from django.db.models import signals
from job.models import JobDef, JobRun, JobPayload, JobVariable, JobArtifact
from project.models import Project
from package.models import Package
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership, User
from workspace.models import Workspace
from workspace.listeners import install_demo_project_in_workspace
from django.conf import settings


class BaseJobTestDef:
    def file_to_bytes(self, fp):
        with fp:
            return fp.read()

    @classmethod
    def setup_class(cls):
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)
        cls.users = {
            "admin": User.objects.create(
                username="admin",
                is_staff=True,
                is_superuser=True,
                email="admin@askanna.dev",
            ),
            "user": User.objects.create(username="user", email="user@askanna.dev"),
            "user_nonmember": User.objects.create(
                username="user_nonmember", email="user_nonmember@askanna.dev"
            ),
        }

        # setup variables
        cls.workspace = Workspace.objects.create(**{"title": "WorkspaceX",})
        cls.workspace2 = Workspace.objects.create(**{"title": "WorkspaceY",})
        cls.project = Project.objects.create(
            **{"name": "TestProject", "workspace": cls.workspace}
        )
        cls.project2 = Project.objects.create(
            **{"name": "TestProject2", "workspace": cls.workspace2}
        )
        # make the admin user member of the workspace
        cls.admin_member = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace.uuid,
            user=cls.users["admin"],
            role=WS_ADMIN,
        )
        # make the memberA user member of the workspace
        cls.memberA_member = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace.uuid,
            user=cls.users["user"],
            role=WS_MEMBER,
            name="membername",
        )
        # make the memberA user member of the workspace2
        cls.memberA_member2 = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace2.uuid,
            user=cls.users["user"],
            role=WS_MEMBER,
            name="membername2",
        )

        cls.package = Package.objects.create(
            project=cls.project,
            size=1,
            title="TestPackage",
            created_by=cls.users["user"],
        )
        cls.package.write(
            open(settings.TEST_RESOURCES_DIR.path("projects/project-001.zip"), "rb",)
        )

        cls.package2 = Package.objects.create(
            project=cls.project2,
            size=1,
            title="TestPackage2",
            created_by=cls.users["user"],
        )
        cls.package2.write(
            open(settings.TEST_RESOURCES_DIR.path("projects/project-001.zip"), "rb",)
        )

        cls.jobdef = JobDef.objects.create(name="TestJobDef", project=cls.project,)
        cls.jobdef2 = JobDef.objects.create(name="TestJobDef2", project=cls.project2,)
        cls.jobruns = {
            "run1": JobRun.objects.create(
                package=cls.package,
                jobdef=cls.jobdef,
                status="SUBMITTED",
                owner=cls.users["user"],
                member=cls.memberA_member,
            ),
            "run2": JobRun.objects.create(
                package=cls.package,
                jobdef=cls.jobdef,
                status="SUBMITTED",
                owner=cls.users["user"],
                member=cls.memberA_member,
            ),
            "run3": JobRun.objects.create(
                package=cls.package2,
                jobdef=cls.jobdef2,
                status="SUBMITTED",
                owner=cls.users["user"],
                member=cls.memberA_member2,
            ),
        }
        cls.artifact = JobArtifact.objects.create(
            **{"jobrun": cls.jobruns["run1"], "size": 500}
        )
        with open(
            settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip"), "rb"
        ) as f:
            cls.artifact.write(f)

        cls.variable = JobVariable.objects.create(
            **{
                "name": "TestVariable",
                "value": "TestValue",
                "is_masked": False,
                "project": cls.project,
            }
        )

        cls.variable_masked = JobVariable.objects.create(
            **{
                "name": "TestVariableMasked",
                "value": "TestValue",
                "is_masked": True,
                "project": cls.project,
            }
        )

    @classmethod
    def teardown_class(cls):
        """
        Remove all the user instances we had setup for the test
        """
        for _, user in cls.users.items():
            user.delete()
        cls.variable.delete()
        cls.variable_masked.delete()
        cls.workspace.delete()  # this will cascade delete child items
