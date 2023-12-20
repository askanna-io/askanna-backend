from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


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
