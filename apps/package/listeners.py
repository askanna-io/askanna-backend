from zipfile import ZipFile

from django.conf import settings
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from account.models.membership import MSP_WORKSPACE
from core.config import AskAnnaConfig
from job.models import JobDef, ScheduledJob
from package.models import Package
from package.signals import package_upload_finish


@receiver(package_upload_finish)
def package_upload_extract_zip(sender, signal, postheaders, obj, **kwargs):
    # extract from package_root to blob_root under the package uuid
    # this is for the fileview
    target_location = settings.BLOB_ROOT

    source_path = obj.stored_path
    target_path = target_location / str(obj.uuid)

    with ZipFile(source_path, mode="r") as zip_package:
        zip_package.extractall(path=target_path)


@receiver(package_upload_finish)
def package_upload_extract_jobs_from_askannayml(sender, signal, postheaders, obj, **kwargs):
    """
    Extract jobs defined in the askanna.yml (if set)

    The `askanna.yml` file should be located in the root level of the archive
    """
    source_path = obj.stored_path

    # Read the zipfile and find askanna.yml
    with ZipFile(source_path) as zip_obj:
        askannayml_files = {"askanna.yml", "askanna.yaml"}
        found_askannayml = askannayml_files - (askannayml_files - set(zip_obj.namelist()))
        yml_found_in_set = len(found_askannayml) > 0

        if not yml_found_in_set:
            return

        askannayml = zip_obj.read(list(found_askannayml)[0])

    config_from_askannayml = AskAnnaConfig.from_stream(askannayml)
    if config_from_askannayml is None:
        return

    project = obj.project

    # create or find jobdef for each found jobs
    for _, job in config_from_askannayml.jobs.items():
        jd, _ = JobDef.objects.get_or_create(name=job.name, project=project)

        # update the jobdef.environment_image and timezone
        jd.environment_image = job.environment.image
        jd.timezone = job.timezone
        jd.deleted_at = None  # restore the deleted job if this was set
        jd.save(
            update_fields=[
                "environment_image",
                "timezone",
                "deleted_at",
                "modified_at",
            ]
        )

        # check what existing schedules where and store the last_run_at and raw_definition
        old_rules = ScheduledJob.objects.filter(job=jd)
        old_schedules = []
        for schedule in old_rules:
            old_schedules.append(
                {
                    "last_run_at": schedule.last_run_at,
                    "raw_definition": schedule.raw_definition,
                }
            )

        # clear existing schedules
        old_rules.delete()

        for schedule in job.schedules:
            # create scheduled job
            new_schedule_def = {
                "job": jd,
                "raw_definition": schedule.raw_definition,
                "cron_definition": schedule.cron_definition,
                "cron_timezone": schedule.cron_timezone,
                "member": obj.created_by_member,
            }
            last_run_at = [
                old.get("last_run_at") for old in old_schedules if old.get("raw_definition") == schedule.raw_definition
            ]
            if len(last_run_at) > 0:
                new_schedule_def["last_run_at"] = last_run_at[0]
            scheduled_job = ScheduledJob.objects.create(**new_schedule_def)
            scheduled_job.update_next()


@receiver(pre_delete, sender=Package)
def delete_package(sender, instance: Package, **kwargs):
    instance.prune()


@receiver(pre_save, sender=Package)
def add_member_to_package(sender, instance: Package, **kwargs):
    """
    On creation or update of a package, add the member to it who created this. We already have the user, but we lookup
    the membership for it. We know this by project->workspace.

    We only know the instance.created_by when an upload was finished. So this signal is executed twice, but we only
    update when the created_by is filled
    """
    if instance.created_by_user and (not instance.created_by_member):
        membership = instance.created_by_user.memberships.filter(
            object_uuid=instance.project.workspace.uuid,  # type: ignore
            object_type=MSP_WORKSPACE,
            deleted_at__isnull=True,
        ).first()
        if membership:
            instance.created_by_member = membership
