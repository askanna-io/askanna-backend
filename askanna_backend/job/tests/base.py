from job.models import JobDef, JobRun, JobPayload, JobVariable, JobArtifact
from project.models import Project
from package.models import Package
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership, User
from workspace.models import Workspace
from django.conf import settings


class BaseJobTestDef:
    @classmethod
    def setup_class(cls):
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
        cls.project = Project.objects.create(
            **{"name": "TestProject", "workspace": cls.workspace}
        )
        cls.package = Package.objects.create(
            project=cls.project, size=1, title="TestPackage"
        )
        cls.jobdef = JobDef.objects.create(name="TestJobDef", project=cls.project,)
        cls.jobruns = {
            "run1": JobRun.objects.create(
                package=cls.package, jobdef=cls.jobdef, status="SUBMITTED"
            ),
            "run2": JobRun.objects.create(
                package=cls.package, jobdef=cls.jobdef, status="SUBMITTED"
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
        # make the admin user member of the workspace
        admin_member = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace.uuid,
            user=cls.users["admin"],
            role=WS_ADMIN,
        )
        # make the memberA user member of the workspace
        memberA_member = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace.uuid,
            user=cls.users["user"],
            role=WS_MEMBER,
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
