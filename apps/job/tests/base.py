from django.conf import settings
from django.db.models import signals
from django.utils import timezone

from core.tests.base import BaseUserPopulation
from job.models import JobDef, RunImage
from package.models import Package
from project.models import Project
from run.models import Run
from workspace.listeners import install_demo_project_in_workspace
from workspace.models import Workspace


class BaseJobTestDef(BaseUserPopulation):
    def setUp(self):
        super().setUp()
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)
        self.project = Project.objects.create(**{"name": "TestProject", "workspace": self.workspace_a})
        self.project2 = Project.objects.create(**{"name": "TestProject2", "workspace": self.workspace_b})
        self.project3 = Project.objects.create(
            **{
                "name": "TestProject3",
                "workspace": self.workspace_c,  # This workspace is PUBLIC
                "visibility": "PUBLIC",
            }
        )
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
                created_by_member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
            "run4": Run.objects.create(
                name="run4",
                description="test run4",
                package=self.package2,
                jobdef=self.jobdef2,
                status="SUBMITTED",
                created_by_user=self.users.get("member"),
                created_by_member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
            "run5": Run.objects.create(
                name="run5",
                description="test run5",
                package=self.package,
                jobdef=self.jobdef,
                status="IN_PROGRESS",
                created_by_user=self.users.get("member"),
                created_by_member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
            "run6": Run.objects.create(
                name="run6",
                description="test run6",
                package=self.package,
                jobdef=self.jobdef_public,
                status="IN_PROGRESS",
                created_by_user=self.users.get("member"),
                created_by_member=self.members_workspace2.get("member"),
                run_image=self.run_image,
                started_at=timezone.now(),
            ),
            "run7": Run.objects.create(
                name="",
                description="",
                package=self.package,
                jobdef=self.jobdef,
                status="FAILED",
                created_by_user=self.users.get("member"),
                created_by_member=self.members_workspace2.get("member"),
                run_image=self.run_image,
            ),
        }

    def tearDown(self):
        """
        Remove all the user instances we had setup for the test
        """
        super().tearDown()
