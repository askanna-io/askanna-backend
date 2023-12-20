import logging

import django.db.models.deletion
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import migrations, models

from account.models import User
from core.models import ObjectReference
from run.models import RunArtifact
from storage.models import File
from storage.utils.file import get_md5_from_file

logger = logging.getLogger(__name__)

artifact_root_path = settings.STORAGE_ROOT / "artifacts"


def move_run_artifact_files(apps, schema_editor):
    run_artifacts = RunArtifact.objects.all()

    if not run_artifacts.exists():
        logger.info("No run artifacts found, nothing to do")
        return

    if not artifact_root_path.exists():
        logger.info(f"Artifacts root directory '{artifact_root_path}' does not exist, nothing to do")
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

                content_file = ContentFile(artifact_file.read_bytes(), name=artifact_file.name)

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

    for project_directory in artifact_root_path.iterdir():
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
        artifact_root_path.rmdir()
    except OSError:
        logger.info(f"Artifact root directory '{artifact_root_path}' is not empty, not removing it")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_objectreference_add_run_artifact"),
        ("run", "0003_rename_runartifact_fields_and_delete_chunkedrunartifactpart"),
        ("storage", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="runartifact",
            name="artifact_file",
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="artifact_file", to="storage.file"
            ),
        ),
        migrations.RunPython(move_run_artifact_files, migrations.RunPython.noop, elidable=True),
    ]
