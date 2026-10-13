import json
import unittest
from pathlib import Path

from src.mod_package_passport import build_passport_metadata, validate_passport


class ModPackagePassportTests(unittest.TestCase):
    def setUp(self):
        self.passport = json.loads((Path(__file__).parents[1] / "research/external/SHROUDFORGE_PACKAGE_PASSPORT_FIXTURE_20261013.json").read_text())

    def test_shroudforge_passport_is_review_required_and_read_only(self):
        self.assertEqual(validate_passport(self.passport), [])
        result = build_passport_metadata(self.passport)
        self.assertEqual(result["state"], "review-required")
        self.assertTrue(result["read_only"])
        self.assertFalse(result["executes_package"])
        self.assertFalse(result["runtime_approval"])
        self.assertEqual(len(result["passport_sha256"]), 64)

    def test_missing_hash_blocks_passport(self):
        invalid = {**self.passport, "files": [{"path": "mod.json"}]}
        result = build_passport_metadata(invalid)
        self.assertEqual(result["state"], "blocked")
        self.assertTrue(result["issues"])


if __name__ == "__main__":
    unittest.main()
