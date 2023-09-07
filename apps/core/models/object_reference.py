from __future__ import annotations

import uuid as _uuid

from django.core.cache import cache
from django.db import models


class ObjectReference(models.Model):
    """
    ObjectReference is a model to refer to any object in the database.

    When a reference is created, it comes with a UUID and the referenced object is stored in the correct field. This
    way we can refer to any object in the database as long as we have created a field for it in this model.

    This reference can be used in other models that refer to other objects in the database. Especially where this
    model wants to reference objects in multiple other models.

    We did not use Django's GenericForeignKey because we wanted to be able to use the database relations to reference
    objects without needing to look up the relation definition in the Python code. This is not possible with Django's
    GenericForeignKey.
    """

    uuid = models.UUIDField(primary_key=True, default=_uuid.uuid4, editable=False, verbose_name="UUID")

    account_user = models.OneToOneField("account.User", blank=True, null=True, on_delete=models.CASCADE)
    account_membership = models.OneToOneField("account.Membership", blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"Object: {repr(self.object)}"

    def save(self, *args, **kwargs):
        assert self.object is not None, "One field should be set"
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<Object: {repr(self.object)}>"

    @property
    def object(self):
        fields_with_value = [
            getattr(self, field.name)
            for field in self._meta.get_fields()
            if field.name in ["account_user", "account_membership"] and getattr(self, field.name)
        ]

        assert len(fields_with_value) == 1, "One field and only one field should be set"

        return fields_with_value[0]

    @property
    def object_type(self) -> str:
        return f"{self.object._meta.app_label}.{self.object._meta.object_name}"

    @classmethod
    def get_or_create(cls, object: int | _uuid.UUID | models.Model) -> tuple[ObjectReference, bool]:
        assert isinstance(object, models.Model), "object_type should be set if object is not a model"

        object_type = f"{object._meta.app_label}.{object._meta.object_name}"

        object_field = object_type.lower().replace(".", "_")
        assert hasattr(cls, object_field), f"{object_type} is not (yet) an available object in model core.Object"

        return cache.get_or_set(
            f"core.Object_{object_field}_{object.suuid}",  # type: ignore
            lambda: cls.objects.get_or_create(**{object_field: object}),  # type: ignore
        )
