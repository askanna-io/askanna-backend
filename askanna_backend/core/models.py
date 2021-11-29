# -*- coding: utf-8 -*-
import os
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import (
    ActivatorModel,
    TimeStampedModel,
)
from django_cryptography.fields import encrypt

from .utils import GoogleTokenGenerator


class DeletedModel(models.Model):
    """
    Defines an additional field to registere when the model is deleted
    """

    deleted = models.DateTimeField(
        blank=True, auto_now_add=False, auto_now=False, null=True
    )

    def to_deleted(self):
        self.deleted = timezone.now()
        self.save(update_fields=["deleted"])

    class Meta:
        abstract = True


class DescriptionModel(models.Model):
    """
    DescriptionModel

    An abstract base class model that provides a description field.
    """

    description = models.TextField(_("description"), blank=True, null=True)

    class Meta:
        abstract = True


class NameModel(models.Model):
    """
    NameModel

    An abstract base class model that provides a name field.
    """

    name = models.CharField(_("name"), max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class NameDescriptionModel(NameModel, DescriptionModel):
    class Meta:
        abstract = True


class SlimBaseModel(TimeStampedModel, DeletedModel, models.Model):

    uuid = models.UUIDField(
        primary_key=True, db_index=True, editable=False, default=uuid.uuid4
    )
    short_uuid = models.CharField(max_length=32, blank=True, unique=True)

    def save(self, *args, **kwargs):
        # Manually set the uuid and short_uuid
        if not self.uuid:
            self.uuid = uuid.uuid4()
        if not self.short_uuid and self.uuid:
            # FIXME: mode this part of code outside save to check for potential collision in existing set
            google_token = GoogleTokenGenerator()
            self.short_uuid = google_token.create_token(uuid_in=self.uuid)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class SlimBaseForAuthModel(SlimBaseModel):

    uuid = models.UUIDField(db_index=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True


class BaseModel(NameDescriptionModel, SlimBaseModel):
    class Meta:
        abstract = True
        ordering = ["-modified"]


class ActivatedModel(ActivatorModel, BaseModel):
    class Meta:
        abstract = True


class AuthorModel(models.Model):
    """
    Adding created_by to the model to register who created this instance
    """

    created_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        abstract = True


class ArtifactModelMixin:
    """
    Providing basic accessors to the file on the filesystem related to the model
    """

    filetype = "file"
    filextension = "justafile"
    filereadmode = "r"
    filewritemode = "w"

    @property
    def storage_location(self):
        return self.get_storage_location()

    def get_storage_location(self):
        raise NotImplementedError(
            f"Please implement 'get_storage_location' for {self.__class__.__name__}"
        )

    def get_base_path(self):
        raise NotImplementedError(
            f"Please implement 'get_full_path' for {self.__class__.__name__}"
        )

    def get_full_path(self):
        raise NotImplementedError(
            f"Please implement 'get_base_path' for {self.__class__.__name__}"
        )

    @property
    def stored_path(self):
        return self.get_full_path()

    @property
    def filename(self):
        return "{}_{}.{}".format(self.filetype, self.uuid.hex, self.filextension)

    def get_name(self):
        return self.filename

    @property
    def read(self):
        with open(self.stored_path, self.filereadmode) as f:
            return f.read()

    def write(self, stream):
        """
        Write contents to the filesystem
        """
        os.makedirs(self.get_base_path(), exist_ok=True)
        with open(self.stored_path, self.filewritemode) as f:
            f.write(stream.read())

    def prune(self):
        try:
            os.remove(self.stored_path)
        except FileNotFoundError:
            pass


class Setting(SlimBaseModel):
    name = models.CharField(max_length=32, blank=True, unique=True)
    value = encrypt(models.TextField(default=None, blank=True, null=True))
