from django.db import models

from core.models import BaseModel


class RunArtifactQuerySet(models.QuerySet):
    def active(self, add_select_related: bool = False):
        active_query = self.filter(
            deleted_at__isnull=True,
            artifact_file__deleted_at__isnull=True,
            artifact_file__completed_at__isnull=False,
            run__deleted_at__isnull=True,
            run__jobdef__deleted_at__isnull=True,
            run__jobdef__project__deleted_at__isnull=True,
            run__jobdef__project__workspace__deleted_at__isnull=True,
        ).select_related("artifact_file")

        if add_select_related is True:
            return active_query.select_related(
                "run__jobdef__project__workspace",
                "artifact_file___created_by__account_membership__user",
            )

        return active_query


class RunArtifact(BaseModel):
    """
    Artifact of a run stored into an archive file
    """

    run = models.ForeignKey("run.Run", on_delete=models.CASCADE, related_name="artifacts")
    artifact_file = models.OneToOneField(
        "storage.File", null=True, on_delete=models.CASCADE, related_name="artifact_file"
    )

    objects = RunArtifactQuerySet().as_manager()

    permission_by_action = {
        "list": "project.run.view",
        ("retrieve", "info", "download"): "project.run.view",
        ("create", "upload_part", "upload_complete", "upload_abort"): "project.run.create",
        "partial_update": "project.run.edit",
    }

    @property
    def project(self):
        return self.run.jobdef.project

    @property
    def job(self):
        return self.run.jobdef

    @property
    def upload_directory(self):
        return (
            "runs/"
            + self.run.suuid[:2].lower()
            + "/"
            + self.run.suuid[2:4].lower()
            + "/"
            + self.run.suuid
            + "/artifacts"
        )

    def get_name(self) -> str | None:
        if self.artifact_file:
            return self.artifact_file.name
        return None

    class Meta:
        db_table = "run_artifact"
        get_latest_by = "created_at"
        ordering = ["-created_at"]
