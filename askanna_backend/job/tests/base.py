# -*- coding: utf-8 -*-
import datetime
import io

from django.conf import settings
from django.db.models import signals
from django.utils import timezone


from core.tests.base import BaseUploadTestMixin, BaseUserPopulation  # noqa
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

variable_response_good_small_no_label = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [],
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
metric_response_good_small_no_label = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [],
        "created": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [],
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


class BaseJobTestDef(BaseUserPopulation):
    databases = {"default", "runinfo"}

    def file_to_bytes(self, fp):
        with fp:
            return fp.read()

    def setUp(self):
        super().setUp()
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)
        self.project = Project.objects.create(**{"name": "TestProject", "workspace": self.workspace_a})
        self.project2 = Project.objects.create(**{"name": "TestProject2", "workspace": self.workspace_b})
        self.project3 = Project.objects.create(
            **{
                "name": "TestProject3",
                "workspace": self.workspace_c,
                "visibility": "PUBLIC",
            }
        )  # the workspace is public
        self.package = Package.objects.create(
            original_filename="project-no-yml.zip",
            project=self.project,
            size=1,
            name="TestPackage",
            created_by=self.users.get("member"),
            finished=timezone.now(),
        )
        self.package.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-no-yml.zip"),
                "rb",
            )
        )

        self.package2 = Package.objects.create(
            original_filename="project-001.zip",
            project=self.project2,
            size=1,
            name="TestPackage2",
            created_by=self.users.get("member"),
            finished=timezone.now(),
        )
        self.package2.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-001.zip"),
                "rb",
            )
        )

        self.package3 = Package.objects.create(
            original_filename="project-no-yml.zip",
            project=self.project2,
            size=1,
            name="TestPackage3",
            created_by=self.users.get("member"),
            finished=timezone.now(),
        )
        self.package3.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-no-yml.zip"),
                "rb",
            )
        )

        # this package is visible to everyone
        self.package4 = Package.objects.create(
            original_filename="project-no-yml.zip",
            project=self.project3,
            size=1,
            name="TestPackage4",
            created_by=self.users.get("member"),
            finished=timezone.now(),
        )
        self.package4.write(
            open(
                settings.TEST_RESOURCES_DIR.path("projects/project-no-yml.zip"),
                "rb",
            )
        )

        self.jobdef = JobDef.objects.create(
            name="TestJobDef",
            project=self.project,
        )
        self.jobdef2 = JobDef.objects.create(
            name="my-test-job",
            project=self.project2,
        )
        self.jobdef3 = JobDef.objects.create(
            name="my-test-job3",
            project=self.project2,
        )
        self.jobdef_public = JobDef.objects.create(
            name="my-test-job3",
            project=self.project3,
        )
        self.run_image = RunImage.objects.create(name="TestImage", tag="latest", digest="unknown")
        self.jobruns = {
            "run1": JobRun.objects.create(
                name="run1",
                description="test run1",
                package=self.package,
                jobdef=self.jobdef,
                status="COMPLETED",
                created_by=self.users.get("member"),
                member=self.members.get("member"),
                run_image=self.run_image,
                duration=50646,  # fictive because we don't have access to the handlers here in tests
            ),
            "run2": JobRun.objects.create(
                name="run2",
                description="test run2",
                package=self.package,
                jobdef=self.jobdef,
                status="COMPLETED",
                created_by=self.users.get("member"),
                member=self.members.get("member"),
                run_image=self.run_image,
            ),
            "run3": JobRun.objects.create(
                name="run3",
                description="test run3",
                package=self.package2,
                jobdef=self.jobdef3,  # link faulty job on purpose to test on error not found in askanna.yml
                status="IN_PROGRESS",
                created_by=self.users.get("member"),
                member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
            "run4": JobRun.objects.create(
                name="run4",
                description="test run4",
                package=self.package2,
                jobdef=self.jobdef2,
                status="SUBMITTED",
                created_by=self.users.get("member"),
                member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
            "run5": JobRun.objects.create(
                name="run5",
                description="test run5",
                package=self.package,
                jobdef=self.jobdef,
                status="IN_PROGRESS",
                created_by=self.users.get("member"),
                member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
            "run6": JobRun.objects.create(
                name="run6",
                description="test run6",
                package=self.package,
                jobdef=self.jobdef_public,
                status="IN_PROGRESS",
                created_by=self.users.get("member"),
                member=self.members_workspace2.get("member"),
                run_image=self.run_image,
                started=timezone.now(),
            ),
            "run7": JobRun.objects.create(
                name="",
                description="",
                package=self.package,
                jobdef=self.jobdef,
                status="FAILED",
                created_by=self.users.get("member"),
                member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
        }

        self.runmetrics = {
            "run1": RunMetrics.objects.create(jobrun=self.jobruns["run1"], metrics=metric_response_good, count=4),
            "run2": RunMetrics.objects.create(jobrun=self.jobruns["run2"], metrics=metric_response_bad, count=2),
            "run3": RunMetrics.objects.create(jobrun=self.jobruns["run3"], metrics=metric_response_bad, count=2),
            "run6": RunMetrics.objects.create(
                jobrun=self.jobruns["run6"], metrics=metric_response_good_small_no_label, count=4
            ),
            "run7": RunMetrics.objects.create(jobrun=self.jobruns["run7"], metrics=[]),
        }

        self.runoutput = {
            "run1": JobOutput.objects.get(jobrun=self.jobruns.get("run1")),
            "run2": JobOutput.objects.get(jobrun=self.jobruns.get("run2")),
            "run3": JobOutput.objects.get(jobrun=self.jobruns.get("run3")),
            "run5": JobOutput.objects.get(jobrun=self.jobruns.get("run5")),
        }

        self.runoutput["run1"].stdout = [
            [1, datetime.datetime.utcnow().isoformat(), "some test stdout 1"],
            [2, datetime.datetime.utcnow().isoformat(), "some test stdout 2"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 3"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 4"],
            [5, datetime.datetime.utcnow().isoformat(), "some test stdout 5"],
            [6, datetime.datetime.utcnow().isoformat(), "some test stdout 6"],
        ]
        self.runoutput["run2"].stdout = [
            [1, datetime.datetime.utcnow().isoformat(), "some test stdout 1"],
            [2, datetime.datetime.utcnow().isoformat(), "some test stdout 2"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 3"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 4"],
            [5, datetime.datetime.utcnow().isoformat(), "some test stdout 5"],
            [6, datetime.datetime.utcnow().isoformat(), "some test stdout 6"],
        ]
        self.runoutput["run1"].save(update_fields=["stdout"])
        self.runoutput["run2"].save(update_fields=["stdout"])

        self.runoutput.get("run3").log("some test stdout 1", timestamp=datetime.datetime.utcnow().isoformat())
        self.runoutput.get("run3").log("some test stdout 2")
        self.runoutput.get("run3").log("some test stdout 3")
        self.runoutput.get("run3").log("some test stdout 4", print_log=True)
        self.runoutput.get("run3").log("some test stdout 5", print_log=True)
        self.runoutput.get("run3").log("some test stdout 6", print_log=True)
        self.runoutput.get("run3").log("some test stdout 7", print_log=True)
        self.runoutput.get("run3").log("some test stdout 8", print_log=True)
        self.runoutput.get("run3").log("some test stdout 9", print_log=True)

        self.runoutput.get("run5").log("some test stdout 1", timestamp=datetime.datetime.utcnow().isoformat())
        self.runoutput.get("run5").log("some test stdout 2")
        self.runoutput.get("run5").log("some test stdout 3")
        self.runoutput.get("run5").log("some test stdout 4", print_log=True)
        self.runoutput.get("run5").log("some test stdout 5", print_log=True)
        self.runoutput.get("run5").log("some test stdout 6", print_log=True)
        self.runoutput.get("run5").log("some test stdout 7", print_log=True)
        self.runoutput.get("run5").log("some test stdout 8", print_log=True)
        self.runoutput.get("run5").log("some test stdout 9", print_log=True)

        self.runresults = {
            "run2": RunResult.objects.create(
                name="someresult.txt",
                run=self.jobruns["run2"],
            ),
        }
        self.runresults["run2"].write(io.BytesIO(b"some result content"))

        self.tracked_variables = {
            "run1": RunVariables.objects.get(jobrun=self.jobruns["run1"]),
            "run2": RunVariables.objects.get(jobrun=self.jobruns["run2"]),
            "run3": RunVariables.objects.get(jobrun=self.jobruns["run3"]),
            "run6": RunVariables.objects.get(jobrun=self.jobruns["run6"]),
            "run7": RunVariables.objects.get(jobrun=self.jobruns["run7"]),
        }
        self.tracked_variables["run1"].variables = tracked_variables_response_good
        self.tracked_variables["run2"].variables = tracked_variables_response_good
        self.tracked_variables["run3"].variables = tracked_variables_response_good
        self.tracked_variables["run6"].variables = variable_response_good_small_no_label
        self.tracked_variables["run1"].save()
        self.tracked_variables["run2"].save()
        self.tracked_variables["run3"].save()
        self.tracked_variables["run6"].save()

        self.artifact = JobArtifact.objects.create(**{"jobrun": self.jobruns["run1"], "size": 500})
        with open(settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip"), "rb") as f:
            self.artifact.write(f)

        self.variable = JobVariable.objects.create(
            **{
                "name": "TestVariable",
                "value": "TestValue",
                "is_masked": False,
                "project": self.project,
            }
        )

        self.variable_masked = JobVariable.objects.create(
            **{
                "name": "TestVariableMasked",
                "value": "TestValue",
                "is_masked": True,
                "project": self.project,
            }
        )

    def tearDown(self):
        """
        Remove all the user instances we had setup for the test
        """
        super().tearDown()
        self.variable.delete()
        self.variable_masked.delete()
