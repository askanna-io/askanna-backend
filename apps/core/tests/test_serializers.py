from django.test import TestCase
from rest_framework import serializers

from core.serializers import FlexibleField


class TestFlexibleField(TestCase):
    def setUp(self):
        class TestSerializer(serializers.Serializer):
            field = FlexibleField(allow_null=True)

        self.serializer = TestSerializer()

    def test_to_internal_value(self):
        assert self.serializer.fields["field"].to_internal_value("true") is True
        assert self.serializer.fields["field"].to_internal_value("false") is False
        assert self.serializer.fields["field"].to_internal_value("null") is None
        assert self.serializer.fields["field"].to_internal_value("other") == "other"
        assert self.serializer.fields["field"].to_internal_value(12.34) == 12.34

    def test_to_representation(self):
        assert self.serializer.fields["field"].to_representation("TRUE") is True
        assert self.serializer.fields["field"].to_representation("FALSE") is False
        assert self.serializer.fields["field"].to_representation("NULL") is None
        assert self.serializer.fields["field"].to_representation("OTHER") == "OTHER"
        assert self.serializer.fields["field"].to_representation(12.34) == 12.34
