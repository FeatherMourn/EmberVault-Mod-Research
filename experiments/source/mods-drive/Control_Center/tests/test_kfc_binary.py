import unittest

from core.kfc_binary import BinaryField, BlobReference, FixedArrayLayout, KfcBinaryError, KfcBinaryLayout


class KfcBinaryTests(unittest.TestCase):
    def test_alignment_and_fields(self):
        self.assertEqual(KfcBinaryLayout.align(9, 8), 16)
        KfcBinaryLayout.validate_fields([BinaryField("a", 0, 4), BinaryField("b", 4, 4)], 8)

    def test_rejects_overlap_and_bad_alignment(self):
        with self.assertRaises(KfcBinaryError):
            KfcBinaryLayout.validate_fields([BinaryField("a", 0, 4), BinaryField("b", 2, 4)], 8)
        with self.assertRaises(KfcBinaryError):
            KfcBinaryLayout.validate_fields([BinaryField("a", 2, 4, 4)], 8)

    def test_fixed_array_and_blob_bounds(self):
        KfcBinaryLayout.validate_fixed_array(FixedArrayLayout("entries", 8, 2, 0), 16)
        self.assertEqual(KfcBinaryLayout.resolve_blob(BlobReference("text", 4, 8, 8), 20), (12, 20))
        with self.assertRaises(KfcBinaryError):
            KfcBinaryLayout.resolve_blob(BlobReference("text", 4, 9, 8), 20)


if __name__ == "__main__":
    unittest.main()
