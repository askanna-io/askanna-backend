# -*- coding: utf-8 -*-
import datetime
import io

from django.conf import settings
from django.db.models import signals


from core.tests.base import BaseUploadTestMixin  # noqa
from job.models import (
    JobArtifact,
    JobDef,
    JobRun,
    JobOutput,
    JobVariable,
    RunImage,
    RunMetrics,
    RunResult,
    RunVariables,
)
from project.models import Project
from package.models import Package
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership, User
from workspace.models import Workspace
from workspace.listeners import install_demo_project_in_workspace


tracked_variables_response_good = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Quality", "value": "Good", "type": "string"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Quality", "value": "Ok", "type": "string"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
]

variable_response_good_small = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
]
metric_response_good = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Quality", "value": "Good", "type": "string"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Quality", "value": "Ok", "type": "string"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
]
metric_response_good_reversed = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Quality", "value": "Ok", "type": "string"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Quality", "value": "Good", "type": "string"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
]
metric_response_good_small = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
]
metric_response_bad = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "value": "null"},
        ],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
]


class BaseJobTestDef:
    databases = {"default", "runinfo"}

    def file_to_bytes(self, fp):
        with fp:
            return fp.read()

    @classmethod
    def setup_class(cls):
        signals.post_save.disconnect(
            install_demo_project_in_workspace, sender=Workspace
        )
        cls.users = {
            "anna": User.objects.create(
                username="anna",
                is_staff=True,
                is_superuser=True,
                email="anna@askanna.dev",
            ),
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
        cls.workspace = Workspace.objects.create(**{"name": "WorkspaceX"})
        cls.workspace2 = Workspace.objects.create(**{"name": "WorkspaceY"})
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
            original_filename="project-no-yml.zip",
            project=cls.project,
            size=1,
            name="TestPackage",
            created_by=cls.users["user"],
        )
        cls.package.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-no-yml.zip"),
                "rb",
            )
        )

        cls.package2 = Package.objects.create(
            original_filename="project-001.zip",
            project=cls.project2,
            size=1,
            name="TestPackage2",
            created_by=cls.users["user"],
        )
        cls.package2.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-001.zip"),
                "rb",
            )
        )

        cls.package3 = Package.objects.create(
            original_filename="project-no-yml.zip",
            project=cls.project2,
            size=1,
            name="TestPackage3",
            created_by=cls.users["user"],
        )
        cls.package3.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-no-yml.zip"),
                "rb",
            )
        )

        cls.jobdef = JobDef.objects.create(
            name="TestJobDef",
            project=cls.project,
        )
        cls.jobdef2 = JobDef.objects.create(
            name="my-test-job",
            project=cls.project2,
        )
        cls.jobdef3 = JobDef.objects.create(
            name="my-test-job3",
            project=cls.project2,
        )
        cls.run_image = RunImage.objects.create(
            name="TestImage", tag="latest", digest="unknown"
        )
        cls.jobruns = {
            "run1": JobRun.objects.create(
                name="run1",
                description="test run1",
                package=cls.package,
                jobdef=cls.jobdef,
                status="COMPLETED",
                owner=cls.users["user"],
                member=cls.memberA_member,
                run_image=cls.run_image,
                duration=50646,  # fictive because we don't have access to the handlers here in tests
            ),
            "run2": JobRun.objects.create(
                name="run2",
                description="test run2",
                package=cls.package,
                jobdef=cls.jobdef,
                status="COMPLETED",
                owner=cls.users["user"],
                member=cls.memberA_member,
                run_image=cls.run_image,
            ),
            "run3": JobRun.objects.create(
                name="run3",
                description="test run3",
                package=cls.package2,
                jobdef=cls.jobdef3,
                status="IN_PROGRESS",
                owner=cls.users["user"],
                member=cls.memberA_member2,
                run_image=cls.run_image,
            ),
            "run4": JobRun.objects.create(
                name="run4",
                description="test run4",
                package=cls.package2,
                jobdef=cls.jobdef2,
                status="SUBMITTED",
                owner=cls.users["user"],
                member=cls.memberA_member2,
                run_image=cls.run_image,
            ),
        }
        cls.runmetrics = {
            "run1": RunMetrics.objects.create(
                jobrun=cls.jobruns["run1"], metrics=metric_response_good, count=4
            ),
            "run2": RunMetrics.objects.create(
                jobrun=cls.jobruns["run2"], metrics=metric_response_bad, count=2
            ),
            "run3": RunMetrics.objects.create(
                jobrun=cls.jobruns["run3"], metrics=metric_response_bad, count=2
            ),
        }
        cls.runoutput = {
            "run1": JobOutput.objects.get(jobrun=cls.jobruns.get("run1")),
            "run2": JobOutput.objects.get(jobrun=cls.jobruns.get("run2")),
            "run3": JobOutput.objects.get(jobrun=cls.jobruns.get("run3")),
        }

        cls.runoutput["run1"].stdout = [
            [1, datetime.datetime.utcnow().isoformat(), "some test stdout 1"],
            [2, datetime.datetime.utcnow().isoformat(), "some test stdout 2"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 3"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 4"],
            [5, datetime.datetime.utcnow().isoformat(), "some test stdout 5"],
            [6, datetime.datetime.utcnow().isoformat(), "some test stdout 6"],
        ]
        cls.runoutput["run2"].stdout = [
            [1, datetime.datetime.utcnow().isoformat(), "some test stdout 1"],
            [2, datetime.datetime.utcnow().isoformat(), "some test stdout 2"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 3"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 4"],
            [5, datetime.datetime.utcnow().isoformat(), "some test stdout 5"],
            [6, datetime.datetime.utcnow().isoformat(), "some test stdout 6"],
        ]
        cls.runoutput["run1"].save(update_fields=["stdout"])
        cls.runoutput["run2"].save(update_fields=["stdout"])

        cls.runoutput.get("run3").log(
            "some test stdout 1", timestamp=datetime.datetime.utcnow().isoformat()
        )
        cls.runoutput.get("run3").log("some test stdout 2")
        cls.runoutput.get("run3").log("some test stdout 3")
        cls.runoutput.get("run3").log("some test stdout 4", print_log=True)
        cls.runoutput.get("run3").log("some test stdout 5", print_log=True)
        cls.runoutput.get("run3").log("some test stdout 6", print_log=True)
        cls.runoutput.get("run3").log("some test stdout 7", print_log=True)
        cls.runoutput.get("run3").log("some test stdout 8", print_log=True)
        cls.runoutput.get("run3").log("some test stdout 9", print_log=True)

        cls.runresults = {
            "run2": RunResult.objects.create(
                name="someresult.txt",
                run=cls.jobruns["run2"],
            ),
        }
        cls.runresults["run2"].write(io.BytesIO(b"some result content"))

        cls.tracked_variables = {
            "run1": RunVariables.objects.get(jobrun=cls.jobruns["run1"]),
            "run2": RunVariables.objects.get(jobrun=cls.jobruns["run2"]),
            "run3": RunVariables.objects.get(jobrun=cls.jobruns["run3"]),
        }
        cls.tracked_variables["run1"].variables = tracked_variables_response_good
        cls.tracked_variables["run2"].variables = tracked_variables_response_good
        cls.tracked_variables["run3"].variables = tracked_variables_response_good
        cls.tracked_variables["run1"].save()
        cls.tracked_variables["run2"].save()
        cls.tracked_variables["run3"].save()

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
        cls.workspace2.delete()
