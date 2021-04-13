# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import (
    ArrayField as DjangoArrayField,
    JSONField as DjangoJSONField,
)


class JSONField(DjangoJSONField):
    pass


class ArrayField(DjangoArrayField):
    pass
