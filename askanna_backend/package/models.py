from django.db import models
import uuid

from core.models import BaseModel, SlimBaseModel, AuthorModel


class Package(AuthorModel, BaseModel):
    filename = models.CharField(max_length=500)
   
    # Storage location can also e a bucket location
    # In case of local storage, always relative to the PACKAGES_ROOT, never an abspath
    storage_location = models.CharField(max_length=1000)

    project = models.ForeignKey(
        "project.Project",
        on_delete=models.SET_DEFAULT,
        related_name="packages",
        related_query_name="package",
        null=True,
        blank=True,
        default=None
        )
    size = models.IntegerField(help_text="Size of this package in bytes")

    def unpack(self):
        """
        Extract package and return the path where it can be reached
        Intend to pass the path tho the next worker

        this function will call on a function to read this instance and does the actual unpacking
        """
        pass

    def read_config(self):
        """
        read the config from the package and return the .askanna.yml config as json
        we don't need to extract fully, just list the zip archive and find the files

        only extract specific file for reading (streaming)
        if no config files are found, return emtpy dictionary
        """
        pass

    def unpacked_size(self):
        """
        determine unpacked size, in bytes
        """
        # do something to determine full size, here also no full unpack needed, we need to read the metadata of the zip archive
        return 0

    @property
    def stored_path(self):
        return os.path.join(
            settings.PACKAGES_ROOT, self.storage_location
        )
    class Meta:
        ordering = ['-created']

class ChunkedPackagePart(models.Model):
    uuid = models.UUIDField(primary_key=True, db_index=True, editable=False, default=uuid.uuid4)
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this chunk of the package")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    package = models.ForeignKey(Package, on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]