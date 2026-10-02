import json
import struct
import tempfile
import unittest
from pathlib import Path

from core.enshrouded_save_reader import SaveFormatError, active_character_path, candidate_save_directories, decode_know, discover_save_directories, inspect_save_directory, parse_ksc1_header


class EnshroudedSaveReaderTests(unittest.TestCase):
    def test_discovery_is_read_only_and_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            result = discover_save_directories(home)
            self.assertTrue(result["read_only"])
            self.assertEqual(len(result["candidates"]), len(candidate_save_directories(home)))
            self.assertFalse(any(item["exists"] for item in result["candidates"]))
    def test_directory_inspection_is_read_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "characters-index").write_text('{"latest": 1}', encoding="utf-8")
            payload = b"KSC1" + struct.pack("<I", 0) + b"save-id-12345678"
            (root / "characters-1").write_bytes(payload)
            result = inspect_save_directory(root)
            self.assertTrue(result["read_only"])
            self.assertEqual(result["active_character"], "characters-1")
            self.assertFalse(result["world_save_supported"])
    def test_ksc1_header_is_bounds_checked(self):
        payload = b"compressed"
        data = b"KSC1" + struct.pack("<I", 1) + b"0123456789abcdef" + struct.pack("<I4sI", 7, b"KNOW", len(payload)) + payload
        header = parse_ksc1_header(data)
        self.assertEqual(header.blob_count, 1)
        self.assertEqual(header.blobs[0].owner_id, 7)
        self.assertEqual(header.blobs[0].blob_type, b"KNOW")

    def test_know_pairs_ids_and_values_without_assuming_sorted_ids(self):
        data = struct.pack("<III", 2, 1, 2) + struct.pack("<2I", 99, 3) + struct.pack("<2I", 1, 7)
        self.assertEqual([(e.knowledge_id, e.value) for e in decode_know(data)], [(99, 1), (3, 7)])

    def test_active_character_uses_rolling_index(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            (path / "characters-index").write_text(json.dumps({"latest": 4}), encoding="utf-8")
            self.assertEqual(active_character_path(path), path / "characters-4")

    def test_invalid_index_and_truncated_blob_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            (path / "characters-index").write_text(json.dumps({"latest": 10}), encoding="utf-8")
            with self.assertRaises(SaveFormatError):
                active_character_path(path)
        with self.assertRaises(SaveFormatError):
            parse_ksc1_header(b"KSC1" + b"\x01\x00\x00\x00")


if __name__ == "__main__":
    unittest.main()
