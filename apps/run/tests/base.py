import datetime
import io

from django.conf import settings
from django.utils import timezone

from core.tests.base import BaseUserPopulation
from job.models import JobDef, RunImage
from package.models import Package
from project.models import Project
from run.models import (
    Run,
    RunArtifact,
    RunLog,
    RunMetricMeta,
    RunResult,
    RunVariableMeta,
)

tracked_variables_response_good = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Quality", "value": "Good", "type": "string"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Quality", "value": "Ok", "type": "string"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
]
variable_response_good_small = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
]
variable_response_good_small_no_label = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
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
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Quality", "value": "Good", "type": "string"},
        "label": [
            {"name": "city", "value": "Rotterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Quality", "value": "Ok", "type": "string"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
]
metric_response_good_small = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
]
metric_response_good_small_no_label = [
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
        "label": [],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
        "label": [],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
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
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
    {
        "run_suuid": "aaaa-cccc-eeee-zzzz",
        "metric": {"name": "Accuracy", "value": "0.623"},
        "label": [
            {"name": "city", "value": "Amsterdam", "type": "string"},
            {"name": "product", "value": "TV", "type": "string"},
            {"name": "Missing data", "value": "null"},
        ],
        "created_at": "2021-02-14T12:00:01.123456+00:00",
    },
]


class BaseRunTest(BaseUserPopulation):
    def setUp(self):
        super().setUp()
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
            created_by_user=self.users.get("member"),
            finished_at=timezone.now(),
        )
        self.package.write((settings.TEST_RESOURCES_DIR / "projects" / "project-no-yml.zip").open("rb"))

        self.package2 = Package.objects.create(
            original_filename="project-001.zip",
            project=self.project2,
            size=1,
            name="TestPackage2",
            created_by_user=self.users.get("member"),
            finished_at=timezone.now(),
        )
        self.package2.write((settings.TEST_RESOURCES_DIR / "projects" / "project-001.zip").open("rb"))

        self.package3 = Package.objects.create(
            original_filename="project-no-yml.zip",
            project=self.project2,
            size=1,
            name="TestPackage3",
            created_by_user=self.users.get("member"),
            finished_at=timezone.now(),
        )
        self.package3.write((settings.TEST_RESOURCES_DIR / "projects" / "project-no-yml.zip").open("rb"))

        # this package is visible to everyone
        self.package4 = Package.objects.create(
            original_filename="project-no-yml.zip",
            project=self.project3,
            size=1,
            name="TestPackage4",
            created_by_user=self.users.get("member"),
            finished_at=timezone.now(),
        )
        self.package4.write((settings.TEST_RESOURCES_DIR / "projects" / "project-no-yml.zip").open("rb"))

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
        self.runs = {
            "run1": Run.objects.create(
                name="run1",
                description="test run1",
                package=self.package,
                jobdef=self.jobdef,
                status="COMPLETED",
                created_by_user=self.users.get("member"),
                created_by_member=self.members.get("member"),
                run_image=self.run_image,
                duration=50646,  # fictive because we don't have access to the handlers here in tests
            ),
            "run2": Run.objects.create(
                name="run2",
                description="test run2",
                package=self.package,
                jobdef=self.jobdef,
                status="COMPLETED",
                created_by_user=self.users.get("member"),
                created_by_member=self.members.get("member"),
                run_image=self.run_image,
            ),
            "run3": Run.objects.create(
                name="run3",
                description="test run3",
                package=self.package2,
                jobdef=self.jobdef3,  # link faulty job on purpose to test on error not found in askanna.yml
                status="IN_PROGRESS",
                created_by_user=self.users.get("member"),
                created_by_member=self.members_workspace2.get("member2"),
                run_image=self.run_image,
            ),
            "run4": Run.objects.create(
                name="run4",
                description="test run4",
                package=self.package2,
                jobdef=self.jobdef2,
                status="SUBMITTED",
                created_by_user=self.users.get("member"),
                run_image=self.run_image,
            ),
            "run5": Run.objects.create(
                name="run5",
                description="test run5",
                package=self.package,
                jobdef=self.jobdef,
                status="IN_PROGRESS",
                created_by_user=self.users.get("member"),
                run_image=self.run_image,
            ),
            "run6": Run.objects.create(
                name="run6",
                description="test run6",
                package=self.package,
                jobdef=self.jobdef_public,
                status="IN_PROGRESS",
                created_by_user=self.users.get("member"),
                run_image=self.run_image,
                started_at=timezone.now(),
                trigger="WEBUI",
            ),
            "run7": Run.objects.create(
                name="",
                description="",
                package=self.package,
                jobdef=self.jobdef,
                status="FAILED",
                created_by_user=self.users.get("member"),
                run_image=self.run_image,
                trigger="CLI",
            ),
        }

        self.runmetrics = {
            "run1": RunMetricMeta.objects.create(run=self.runs["run1"], metrics=metric_response_good, count=4),
            "run2": RunMetricMeta.objects.create(run=self.runs["run2"], metrics=metric_response_bad, count=2),
            "run3": RunMetricMeta.objects.create(run=self.runs["run3"], metrics=metric_response_bad, count=2),
            "run6": RunMetricMeta.objects.create(
                run=self.runs["run6"], metrics=metric_response_good_small_no_label, count=4
            ),
            "run7": RunMetricMeta.objects.create(run=self.runs["run7"], metrics=[]),
        }

        self.runlog = {
            "run1": RunLog.objects.get(run=self.runs.get("run1")),
            "run2": RunLog.objects.get(run=self.runs.get("run2")),
            "run3": RunLog.objects.get(run=self.runs.get("run3")),
            "run5": RunLog.objects.get(run=self.runs.get("run5")),
        }

        self.runlog["run1"].stdout = [  # type: ignore
            [1, datetime.datetime.utcnow().isoformat(), "some test stdout 1"],
            [2, datetime.datetime.utcnow().isoformat(), "some test stdout 2"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 3"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 4"],
            [5, datetime.datetime.utcnow().isoformat(), "some test stdout 5"],
            [6, datetime.datetime.utcnow().isoformat(), "some test stdout 6"],
        ]
        self.runlog["run2"].stdout = [  # type: ignore
            [1, datetime.datetime.utcnow().isoformat(), "some test stdout 1"],
            [2, datetime.datetime.utcnow().isoformat(), "some test stdout 2"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 3"],
            [3, datetime.datetime.utcnow().isoformat(), "some test stdout 4"],
            [5, datetime.datetime.utcnow().isoformat(), "some test stdout 5"],
            [6, datetime.datetime.utcnow().isoformat(), "some test stdout 6"],
        ]
        self.runlog["run1"].save(update_fields=["stdout"])
        self.runlog["run2"].save(update_fields=["stdout"])

        self.runlog["run3"].log("some test stdout 1", timestamp=datetime.datetime.utcnow().isoformat())
        self.runlog["run3"].log("some test stdout 2")
        self.runlog["run3"].log("some test stdout 3")
        self.runlog["run3"].log("some test stdout 4")
        self.runlog["run3"].log("some test stdout 5")
        self.runlog["run3"].log("some test stdout 6")
        self.runlog["run3"].log("some test stdout 7")
        self.runlog["run3"].log("some test stdout 8")
        self.runlog["run3"].log("some test stdout 9")

        self.runlog["run5"].log("some test stdout 1", timestamp=datetime.datetime.utcnow().isoformat())
        self.runlog["run5"].log("some test stdout 2")
        self.runlog["run5"].log("some test stdout 3")
        self.runlog["run5"].log("some test stdout 4")
        self.runlog["run5"].log("some test stdout 5")
        self.runlog["run5"].log("some test stdout 6")
        self.runlog["run5"].log("some test stdout 7")
        self.runlog["run5"].log("some test stdout 8")
        self.runlog["run5"].log("some test stdout 9")

        self.runresults = {
            "run2": RunResult.objects.create(
                name="someresult.txt",
                run=self.runs["run2"],
            ),
        }
        self.runresults["run2"].write(io.BytesIO(b"some result content"))

        self.tracked_variables = {
            "run1": RunVariableMeta.objects.get(run=self.runs["run1"]),
            "run2": RunVariableMeta.objects.get(run=self.runs["run2"]),
            "run3": RunVariableMeta.objects.get(run=self.runs["run3"]),
            "run6": RunVariableMeta.objects.get(run=self.runs["run6"]),
            "run7": RunVariableMeta.objects.get(run=self.runs["run7"]),
        }
        self.tracked_variables["run1"].variables = tracked_variables_response_good
        self.tracked_variables["run2"].variables = tracked_variables_response_good
        self.tracked_variables["run3"].variables = tracked_variables_response_good
        self.tracked_variables["run6"].variables = variable_response_good_small_no_label
        self.tracked_variables["run1"].save()
        self.tracked_variables["run2"].save()
        self.tracked_variables["run3"].save()
        self.tracked_variables["run6"].save()

        self.artifact = RunArtifact.objects.create(**{"run": self.runs["run1"], "size": 500})
        self.artifact.write((settings.TEST_RESOURCES_DIR / "artifacts" / "artifact-aa.zip").open("rb"))

    def tearDown(self):
        """
        Remove all the user instances we had setup for the test
        """
        super().tearDown()
