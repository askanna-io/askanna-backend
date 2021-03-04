# -*- coding: utf-8 -*-
import uuid
import unittest

from core.utils import GoogleTokenGenerator


class TestSUUIDGenerator(unittest.TestCase):
    def test_generate_suuid(self):
        generator = GoogleTokenGenerator()
        uuid_original = uuid.UUID("90d1adc2-6833-4c9a-a54f-f21f9dbf0640")
        suuid = generator.create_token(uuid_in=uuid_original)
        self.assertEqual(suuid, "4PGi-Y4Zs-xGZB-E9GF")
