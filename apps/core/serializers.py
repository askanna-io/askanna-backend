from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.STR)
class ReadWriteSerializerMethodField(serializers.Field):
    """
    Code inspired by https://stackoverflow.com/questions/40555472/django-rest-serializer-method-writable-field
    """

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs["source"] = "*"
        kwargs["read_only"] = False
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        if self.method_name is None:
            self.method_name = f"get_{field_name}"
        super().bind(field_name, parent)

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)

    def to_internal_value(self, data):
        return {self.field_name: data}


@extend_schema_field(OpenApiTypes.ANY)
class FlexibleField(serializers.Field):
    TRUE_VALUES = {"true", "True", "TRUE", True}
    FALSE_VALUES = {"false", "False", "FALSE", False}
    NULL_VALUES = {"null", "Null", "NULL", "", None}

    def to_internal_value(self, data):
        if data in self.TRUE_VALUES:
            return True
        if data in self.FALSE_VALUES:
            return False
        if data in self.NULL_VALUES and self.allow_null:
            return None

        return data

    def to_representation(self, value):
        if value in self.TRUE_VALUES:
            return True
        if value in self.FALSE_VALUES:
            return False
        if value in self.NULL_VALUES and self.allow_null:
            return None

        return value


class RelationSerializer(serializers.Serializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()

    def get_relation(self, instance) -> str:
        return instance._meta.model_name

    def get_name(self, instance) -> str:
        if hasattr(instance, "get_name"):
            return instance.get_name()
        return instance.name


class LabelSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    value = FlexibleField(required=False, default=None)
    type = serializers.CharField(required=True)
