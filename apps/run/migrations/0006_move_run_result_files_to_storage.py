import logging

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import migrations

from account.models import Membership, User
from core.models import ObjectReference
from run.models import Run
from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file

logger = logging.getLogger(__name__)


def move_run_result_files(apps, schema_editor):
    result_root_path = settings.STORAGE_ROOT / "artifacts"

    run_results = apps.get_model("run", "RunResult").objects.all()

    if not run_results.exists():
        logger.info("No run results found, nothing to do")
        return

    if not result_root_path.exists():
        logger.info(f"Results root directory '{result_root_path}' does not exist, nothing to do")
        return

    user_anna = User.objects.get(username="anna")

    for run_result in run_results:
        run_result_path = (
            result_root_path
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
                    size=result_file.stat().st_size,
                    etag=get_md5_from_file(content_file),
                    content_type=get_content_type_from_file(content_file),
                    file=content_file,
                    created_for=run_result.run,
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

    for project_directory in result_root_path.iterdir():
        if not project_directory.is_dir():
            continue

        for jobdef_directory in project_directory.iterdir():
            if not jobdef_directory.is_dir():
                continue

            for run_directory in jobdef_directory.iterdir():
                if not run_directory.is_dir():
                    continue

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
        result_root_path.rmdir()
    except OSError:
        logger.info(f"Result root directory '{result_root_path}' is not empty, not removing it")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_objectreference_add_run_run_and_run_artifact"),
        ("run", "0005_run_result_alter_runresult_run_and_more"),
        ("storage", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(move_run_result_files, migrations.RunPython.noop, elidable=True),
    ]
