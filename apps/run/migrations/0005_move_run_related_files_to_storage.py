import logging

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import migrations

from account.models import Membership, User
from core.models import ObjectReference
from run.models import Run, RunArtifact
from run.utils import (
    update_run_metrics_file_and_meta,
    update_run_variables_file_and_meta,
)
from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file

logger = logging.getLogger(__name__)

artifact_root_path = settings.STORAGE_ROOT / "artifacts"
payload_root_path = settings.STORAGE_ROOT / "projects/payloads"


def move_run_payload_files(apps, schema_editor):
    if not payload_root_path.exists():
        logger.info(f"Payload root directory '{payload_root_path}' does not exist, nothing to do")
        return

    run_payloads = apps.get_model("job", "JobPayload").objects.all()

    if not run_payloads.exists():
        logger.info("No run payloads found, nothing to do")
        return

    user_anna = User.objects.get(username="anna")

    runs_with_payload = Run.objects.filter(archive_job_payload__isnull=False)

    for run_with_payload in runs_with_payload:
        run_payload_path = (
            payload_root_path
            / str(run_with_payload.archive_job_payload.jobdef.project.uuid.hex)
            / str(run_with_payload.archive_job_payload.suuid)
        )

        if run_payload_path.exists():
            payload_file = run_payload_path / "payload.json"
            if payload_file.exists():
                if run_with_payload.archive_job_payload.owner:
                    created_by = User.objects.get(uuid=run_with_payload.archive_job_payload.owner.uuid)
                else:
                    created_by = user_anna

                # Make sure we have an ObjectReference for run and created_by
                ObjectReference.get_or_create(object=run_with_payload)
                ObjectReference.get_or_create(object=created_by)

                content_file = ContentFile(
                    payload_file.read_bytes(),
                    name="payload.json",
                )

                file = File.objects.create(
                    name="payload.json",
                    description="",
                    size=payload_file.stat().st_size,
                    etag=get_md5_from_file(content_file),
                    content_type=get_content_type_from_file(content_file),
                    file=content_file,
                    created_for=run_with_payload,
                    created_by=created_by,
                    created_at=run_with_payload.created_at,
                    modified_at=run_with_payload.modified_at,
                    completed_at=run_with_payload.modified_at,
                )

                run_with_payload.payload = file
                run_with_payload.save(update_fields=["payload"])

                payload_file.unlink()
            else:
                logger.info(
                    f"Payload file '{payload_file}' for run '{run_with_payload.suuid}' does not exist, cannot move "
                    "the payload file."
                )
        else:
            logger.info(
                f"Payload path '{run_payload_path}' for run '{run_with_payload.suuid}' does not exist, cannot move "
                "the payload file."
            )


def move_run_artifact_files(apps, schema_editor):
    if not artifact_root_path.exists():
        logger.info(f"Artifacts root directory '{artifact_root_path}' does not exist, nothing to do")
        return

    run_artifacts = RunArtifact.objects.all()

    if not run_artifacts.exists():
        logger.info("No run artifacts found, nothing to do")
        return

    user_anna = User.objects.get(username="anna")

    for run_artifact in run_artifacts:
        run_artifact_path = (
            artifact_root_path
            / str(run_artifact.run.jobdef.project.uuid.hex)
            / str(run_artifact.run.jobdef.uuid.hex)
            / str(run_artifact.run.uuid.hex)
        )

        if run_artifact_path.exists():
            artifact_file = run_artifact_path / f"artifact_{run_artifact.uuid.hex}.zip"
            if artifact_file.exists():
                # Historically we used the created_by_user field to indicate who created the run and created_by_member
                # was later introduced. If the created_by_member is set we use this value, else we switch to the
                # created_by_user value.
                #
                # For even older run artifacts where we did not store the created_by_x we use the project's
                # created_by_user. And if we also don't have a project created_by_user we use the user 'anna'
                # indicating that it was created before we logged who created a run.
                created_by = run_artifact.run.created_by_member or run_artifact.run.created_by_user
                if created_by is None:
                    if run_artifact.run.jobdef.project and run_artifact.run.jobdef.project.created_by_user:
                        created_by = run_artifact.run.jobdef.project.created_by_user
                    else:
                        created_by = user_anna

                # Make sure we have an ObjectReference for run_artifact and created_by
                ObjectReference.get_or_create(object=run_artifact)
                ObjectReference.get_or_create(object=created_by)

                content_file = ContentFile(
                    artifact_file.read_bytes(),
                    name=artifact_file.name,
                )

                file = File.objects.create(
                    name=artifact_file.name,
                    description="",
                    size=artifact_file.stat().st_size,
                    etag=get_md5_from_file(content_file),
                    content_type="application/zip",
                    file=content_file,
                    created_for=run_artifact,
                    created_by=created_by,
                    created_at=run_artifact.created_at,
                    modified_at=run_artifact.modified_at,
                    completed_at=run_artifact.modified_at,
                )

                run_artifact.artifact_file = file
                run_artifact.save(update_fields=["artifact_file"])

                artifact_file.unlink()
            else:
                logger.info(
                    f"Artifact file '{artifact_file}' for run '{run_artifact.run.suuid}' does not exist, cannot move "
                    "the artifact file."
                )
        else:
            logger.info(
                f"Artifact path '{run_artifact_path}' for run '{run_artifact.run.suuid}' does not exist, cannot move "
                "the artifact file."
            )


def move_run_result_files(apps, schema_editor):
    if not artifact_root_path.exists():
        logger.info(f"Results root directory '{artifact_root_path}' does not exist, nothing to do")
        return

    run_results = apps.get_model("run", "RunResult").objects.all()

    if not run_results.exists():
        logger.info("No run results found, nothing to do")
        return

    user_anna = User.objects.get(username="anna")

    for run_result in run_results:
        run_result_path = (
            artifact_root_path
            / str(run_result.run.jobdef.project.uuid.hex)
            / str(run_result.run.jobdef.uuid.hex)
            / str(run_result.run.uuid.hex)
        )

        if run_result_path.exists():
            result_file = run_result_path / f"result_{run_result.uuid.hex}.output"
            if result_file.exists():
                run = Run.objects.get(uuid=run_result.run.uuid)

                # Historically we used the created_by_user field to indicate who created the run and created_by_member
                # was later introduced. If the created_by_member is set we use this value, else we switch to the
                # created_by_user value.
                #
                # For even older run artifacts where we did not store the created_by_x we use the project's
                # created_by_user. And if we also don't have a project created_by_user we use the user 'anna'
                # indicating that it was created before we logged who created a run.
                if run_result.run.created_by_member:
                    created_by = Membership.objects.get(uuid=run_result.run.created_by_member.uuid)
                elif run_result.run.created_by_user:
                    created_by = User.objects.get(uuid=run_result.run.created_by_user.uuid)
                elif run_result.run.jobdef.project and run_result.run.jobdef.project.created_by_user:
                    created_by = User.objects.get(uuid=run_result.run.jobdef.project.created_by_user.uuid)
                else:
                    created_by = user_anna

                # Make sure we have an ObjectReference for run and created_by
                ObjectReference.get_or_create(object=run)
                ObjectReference.get_or_create(object=created_by)

                content_file = ContentFile(
                    result_file.read_bytes(),
                    name=run_result.name if run_result.name else f"result_{run_result.uuid.hex}.json",
                )

                file = File.objects.create(
                    name=run_result.name if run_result.name else f"result_{run_result.uuid.hex}.json",
                    description="",
                    file=content_file,
                    size=result_file.stat().st_size,
                    etag=get_md5_from_file(content_file),
                    content_type=get_content_type_from_file(content_file),
                    upload_to=run.upload_result_directory,
                    created_for=run,
                    created_by=created_by,
                    created_at=run_result.created_at,
                    modified_at=run_result.modified_at,
                    completed_at=run_result.modified_at,
                )

                run.result = file
                run.save(update_fields=["result"])

                result_file.unlink()
            else:
                logger.info(
                    f"Result file '{result_file}' for run '{run_result.run.suuid}' does not exist, cannot move "
                    "the result file."
                )
        else:
            logger.info(
                f"Result path '{run_result_path}' for run '{run_result.run.suuid}' does not exist, cannot move "
                "the result file."
            )


def recreate_run_metric_and_variable_files(apps, schema_editor):
    runs = Run.objects.all()

    for run in runs:
        user_anna = User.objects.get(username="anna")
        # Historically we used the created_by_user field to indicate who created the run and created_by_member
        # was later introduced. If the created_by_member is set we use this value, else we switch to the
        # created_by_user value.
        #
        # For even older run artifacts where we did not store the created_by_x we use the project's
        # created_by_user. And if we also don't have a project created_by_user we use the user 'anna'
        # indicating that it was created before we logged who created a run.
        if run.created_by_member:
            created_by = Membership.objects.get(uuid=run.created_by_member.uuid)
        elif run.created_by_user:
            created_by = User.objects.get(uuid=run.created_by_user.uuid)
        elif run.jobdef.project and run.jobdef.project.created_by_user:
            created_by = User.objects.get(uuid=run.jobdef.project.created_by_user.uuid)
        else:
            created_by = user_anna

        # Make sure we have an ObjectReference for run and created_by
        ObjectReference.get_or_create(object=run)
        ObjectReference.get_or_create(object=created_by)

        update_run_metrics_file_and_meta(run)
        update_run_variables_file_and_meta(run)


def remove_empty_artifact_root(apps, schema_editor):
    if not artifact_root_path.exists():
        logger.info(f"Artifact root directory '{artifact_root_path}' does not exist, nothing to do")
        return

    for project_directory in artifact_root_path.iterdir():
        if not project_directory.is_dir():
            continue

        for jobdef_directory in project_directory.iterdir():
            if not jobdef_directory.is_dir():
                continue

            for run_directory in jobdef_directory.iterdir():
                if not run_directory.is_dir():
                    continue

                for dir_object in run_directory.iterdir():
                    if (
                        dir_object.is_file()
                        and dir_object.name.startswith("runmetrics")
                        or dir_object.name.startswith("runvariables")
                    ):
                        dir_object.unlink()

                try:
                    run_directory.rmdir()
                except OSError:
                    pass

            try:
                jobdef_directory.rmdir()
            except OSError:
                pass

        try:
            project_directory.rmdir()
        except OSError:
            pass

    try:
        artifact_root_path.rmdir()
    except OSError:
        logger.info(f"Artifact root directory '{artifact_root_path}' is not empty, not removing it")


def remove_empty_payload_root(apps, schema_editor):
    if not payload_root_path.exists():
        logger.info(f"Payload root directory '{payload_root_path}' does not exist, nothing to do")
        return

    for project_directory in payload_root_path.iterdir():
        if not project_directory.is_dir():
            continue

        for payload_directory in project_directory.iterdir():
            if not payload_directory.is_dir():
                continue

            try:
                payload_directory.rmdir()
            except OSError:
                pass

        try:
            project_directory.rmdir()
        except OSError:
            pass

    try:
        payload_root_path.rmdir()
    except OSError:
        logger.info(f"Payload root directory '{payload_root_path}' is not empty, not removing it")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_add_objectreference"),
        ("run", "0004_refactor_models_related_to_storage"),
        ("storage", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(move_run_payload_files, migrations.RunPython.noop, elidable=True),
        migrations.RunPython(move_run_artifact_files, migrations.RunPython.noop, elidable=True),
        migrations.RunPython(move_run_result_files, migrations.RunPython.noop, elidable=True),
        migrations.RunPython(remove_empty_artifact_root, migrations.RunPython.noop, elidable=True),
        migrations.RunPython(remove_empty_payload_root, migrations.RunPython.noop, elidable=True),
        migrations.RunPython(recreate_run_metric_and_variable_files, migrations.RunPython.noop, elidable=True),
    ]
