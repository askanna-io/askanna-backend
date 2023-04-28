from __future__ import annotations

from datetime import datetime
from pathlib import Path

from django.conf import settings
from PIL import Image

from account.signals import avatar_changed_signal
from core.models import BaseModel, FileBaseModel

AVATAR_SPECS = {
    "icon": (60, 60),
    "small": (120, 120),
    "medium": (180, 180),
    "large": (240, 240),
}


class BaseAvatarModel(FileBaseModel):
    """
    BaseAvatarModel is an abstract base class model that can be used to add avatar functionality to a model.

    BaseAvatarModel provides the following functionality:
      - install_default_avatar: installs the default avatar that is defined in settings
      - avatar_path: the path where the avatar image is stored
      - write: writes the avatar to the filesystem on the avatar_path
      - convert_avatar: converts the avatar to several sizes and always saves as PNG
      - delete_avatar: removes the avatar (incl. the several sizes) from the filesystem and installs the default avatar
    """

    file_type = "avatar"
    file_extension = "image"
    file_readmode = "rb"
    file_writemode = "wb"

    @property
    def avatar_path(self) -> Path:
        return self.stored_path

    def get_storage_location(self) -> Path:
        return Path(self.uuid.hex)

    def get_root_location(self) -> Path:
        return settings.AVATARS_ROOT

    @property
    def avatar_cdn_locations(self) -> dict:
        """
        Return a dictionary with the CDN locations for the converted avatar images based on the AVATAR_SPECS keys
        """
        return dict(
            zip(
                AVATAR_SPECS.keys(),
                [self.get_cdn_url(spec_name) for spec_name in AVATAR_SPECS.keys()],
                strict=True,
            )
        )

    def write(self, stream):
        """
        Write contents to the filesystem, as is without changing image format
        """
        super().write(stream)

        # We send a signal that the avatar has changed. Follow-up actions can be taken in the signal receiver, so we
        # don't have to delay the response to the user. A.o. there is a listener that triggers 'convert_avatar'.
        avatar_changed_signal.send(sender=self.__class__, instance=self)

    def convert_avatar(self):
        """
        Convert the avatar to several sizes and always save as PNG
        """
        for spec_name, spec_size in AVATAR_SPECS.items():
            with Image.open(self.stored_path) as im:
                im.thumbnail(spec_size)
                im.save(
                    fp=self.get_root_avatar_spec_path(spec_name),
                    format="png",
                )

    def install_default_avatar(self):
        self.write(settings.USERPROFILE_DEFAULT_AVATAR.open(self.file_readmode))

    def prune(self):
        # First, remove all avatar conversions
        for spec_name, _ in AVATAR_SPECS.items():
            Path.unlink(self.get_root_avatar_spec_path(spec_name), missing_ok=True)

        # Then, remove the original avatar and directory
        super().prune()

    def delete_avatar(self):
        """
        Remove existing avatars from the system for this user and install default avatar.
        """
        self.prune()
        self.install_default_avatar()

    def get_spec_filename(self, spec_name: str) -> str:
        return f"avatar_{self.uuid.hex}_{spec_name}.png"

    def get_avatar_spec_path(self, spec_name: str) -> Path:
        return self.storage_location / self.get_spec_filename(spec_name)

    def get_root_avatar_spec_path(self, spec_name: str) -> Path:
        return self.root_storage_location / self.get_spec_filename(spec_name)

    def get_cdn_url(self, spec_name: str) -> str:
        return "{cdn_url}/files/{avatar_directory}/{file_path}?{timestamp}".format(
            cdn_url=settings.ASKANNA_CDN_URL,
            avatar_directory=settings.AVATARS_DIR_NAME,
            file_path=self.get_avatar_spec_path(spec_name),
            timestamp=datetime.timestamp(self.modified_at),
        )

    class Meta(BaseModel.Meta):
        abstract = True
