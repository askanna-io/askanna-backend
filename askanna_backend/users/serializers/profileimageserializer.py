import base64
import datetime
import io
import binascii
from PIL import Image

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.models import UserProfile


class ProfileImageSerializer(serializers.ModelSerializer):
    """
    This ProfileImageSerializer is used to set the user avatar only
    """

    avatar = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "avatar",
            "short_uuid",
        ]

    def validate_avatar(self, value):
        """
            Validate the content of the avatar, as this is a base64 encoded value, we need to validate
            whether this is an image or not
        """
        datatype, image = value.split(";base64,")
        try:
            image_binary = base64.standard_b64decode(image)
        except binascii.Error as e:
            raise ValidationError("Image is not valid.", e)

        try:
            Image.open(io.BytesIO(image_binary))
        except (TypeError, Exception) as e:
            raise ValidationError("Image is not valid.", e)
        return image_binary

    def save(self):
        """
        Perform save of the avatar if set
        self.validated_data.get('avatar')
        """
        # write away the image
        self.instance.write(io.BytesIO(self.validated_data.get("avatar")))
        super().save()
