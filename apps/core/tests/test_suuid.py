import unittest
import uuid

from core.utils.suuid import bx_encode, create_suuid


class TestSUUIDGenerator(unittest.TestCase):
    def test_generate_suuid(self):
        uuid_original = uuid.UUID("90d1adc2-6833-4c9a-a54f-f21f9dbf0640")
        suuid = create_suuid(uuid=uuid_original)
        self.assertEqual(suuid, "4PGi-Y4Zs-xGZB-E9GF")

    def test_generate_suuid_without_suuid(self):
        suuid = create_suuid()
        self.assertEqual(len(suuid), len("0000-0000-0000-0000"))
        self.assertEqual(suuid.count("-"), 3)
        self.assertEqual(len(suuid.split("-")), 4)

    def test_bx_encode_invalid_int(self):
        with self.assertRaises(TypeError):
            bx_encode("a", "0123456789")

    def test_bx_encode_zero(self):
        self.assertEqual(bx_encode(0, "0123456789"), "0")
