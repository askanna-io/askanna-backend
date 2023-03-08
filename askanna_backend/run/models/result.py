import os

from core.models import BaseModel, NameDescriptionBaseModel
from django.conf import settings
from django.db import models


class RunResult(NameDescriptionBaseModel):
    """
    Includes the result and any other output generated by the job.
    """

    run = models.OneToOneField("run.Run", on_delete=models.CASCADE, related_name="result")
    mime_type = models.CharField(
        max_length=100,
        editable=False,
        blank=True,
        null=True,
        help_text="Storing the mime-type of the output file",
    )
    size = models.PositiveIntegerField(editable=False, default=0, help_text="Size of the result stored")

    @property
    def stored_path(self):
        return os.path.join(settings.ARTIFACTS_ROOT, self.storage_location, self.filename)

    @property
    def storage_location(self):
        return os.path.join(
            self.run.jobdef.project.uuid.hex,
            self.run.jobdef.uuid.hex,
            self.run.uuid.hex,
        )

    @property
    def filename(self):
        return "result_{}.output".format(self.uuid.hex)

    @property
    def extension(self):
        extension = None
        if self.name:
            filename, extension = os.path.splitext(self.name)
            if extension == "":
                extension = filename
            if extension.startswith("."):
                extension = extension[1:]
        else:
            # the result.name is not set, we deal with an older result
            extension = "json"

        return extension

    @property
    def read(self):
        """
        Read the result from filesystem and return
        """
        try:
            with open(self.stored_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return b""

    def write(self, stream):
        """
        Write contents to the filesystem
        """
        os.makedirs(os.path.dirname(self.stored_path), exist_ok=True)

        with open(self.stored_path, "wb") as f:
            f.write(stream.read())

    def prune(self):
        try:
            os.remove(self.stored_path)
        except FileNotFoundError:
            pass

    class Meta:
        db_table = "run_result"
        ordering = ["-created_at"]


class ChunkedRunResultPart(BaseModel):
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this run result")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    runresult = models.ForeignKey("RunResult", on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Run result chunk"
        verbose_name_plural = "Run result chunks"