from django.utils import timezone

from job.models import JobDef, ScheduledJob


def test_upload_directory(test_packages):
    package = test_packages["package_private_1"]
    assert "packages" in package.upload_directory
    assert package.upload_directory.endswith(package.suuid)


def test_get_name(test_packages, test_storage_files):
    package = test_packages["package_private_1"]
    assert package.get_name() == "project_with_config.zip"

    package = test_packages["package_private_4"]
    assert package.get_name() is None


def test_get_askanna_config(test_packages, test_storage_files):
    package = test_packages["package_private_1"]
    assert package.get_askanna_config() is not None

    package = test_packages["package_private_2"]
    assert package.get_askanna_config() is None


def test_extract_jobs_from_askanna_config(test_packages):
    test_packages["package_private_1"].extract_jobs_from_askanna_config()

    project = test_packages["package_private_1"].project
    jobs = JobDef.objects.filter(project=project)
    scheduled_jobs = ScheduledJob.objects.filter(job__project=project)

    assert jobs.count() == 2
    assert scheduled_jobs.count() == 2

    # Set last_run_at to a value, so we can test if after uploading the same package again, the last_run_at is set
    scheduled_job = scheduled_jobs.first()
    assert scheduled_job.last_run_at is None
    scheduled_job_suuid = scheduled_job.suuid
    scheduled_job_last_run_at = timezone.now()
    scheduled_job.last_run_at = scheduled_job_last_run_at
    scheduled_job.save()

    # Upload the same package again to test updating the jobs and job schedules with last_run_at set
    job_suuid = jobs.first().suuid
    test_packages["package_private_1"].extract_jobs_from_askanna_config()

    # Confirm that we did not delete jobs after running extract_jobs_from_askanna_config again
    assert jobs.count() == 2
    assert job_suuid in [job.suuid for job in jobs]

    # Confirm that we deleted old schedules after running extract_jobs_from_askanna_config again, but that we kept the
    # info about the last_run_at for schedules with the same raw_definition
    assert scheduled_jobs.count() == 2
    assert scheduled_job_suuid not in [scheduled_job.suuid for scheduled_job in scheduled_jobs]
    assert scheduled_jobs.filter(last_run_at=scheduled_job_last_run_at).count() == 1
