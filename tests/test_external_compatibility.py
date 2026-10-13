import json
import unittest
from pathlib import Path

from src.external_compatibility import compare_external_metadata


class ExternalCompatibilityTests(unittest.TestCase):
    def test_shroudforge_fixture_is_read_only_and_reports_gaps(self):
        fixture = json.loads((Path(__file__).parents[1] / "research/external/SHROUDFORGE_COMPATIBILITY_FIXTURE_20261013.json").read_text())
        result = compare_external_metadata(fixture["external"], fixture["contract"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["runtime_approval"])
        self.assertEqual(result["matches"], ["manifest", "profile"])
        self.assertEqual(result["state"], "compatible-with-gaps")
        self.assertTrue(any("settings" in gap for gap in result["gaps"]))
        self.assertTrue(any("package" in gap for gap in result["gaps"]))

    def test_missing_fields_are_explicit(self):
        result = compare_external_metadata({}, {"manifest": {"id": True}})
        self.assertEqual(result["state"], "compatible-with-gaps")
        self.assertEqual(len(result["gaps"]), 4)


if __name__ == "__main__":
    unittest.main()
