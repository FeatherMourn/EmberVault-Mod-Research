import json
import unittest
from pathlib import Path

from src.mod_manager_contract import review_mod_manager_request


class ModManagerContractTests(unittest.TestCase):
    def test_discovery_is_read_only_and_does_not_need_approval(self):
        result = review_mod_manager_request({"operation": "discover", "package": {"id": "sf.example"}})
        self.assertEqual(result["state"], "review-required")
        self.assertFalse(result["approval_required"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["executes_installation"])

    def test_update_requires_verified_backup(self):
        result = review_mod_manager_request({"operation": "stage-update", "package": {"id": "sf.example"}})
        self.assertEqual(result["state"], "blocked")
        self.assertIn("backup", result["issues"][0])
        self.assertTrue(result["approval_required"])
        self.assertTrue(result["save_manager_backup_authority"])

    def test_fixture_corpus_is_present(self):
        path = Path(__file__).parents[1] / "research/external/SHROUDFORGE_MOD_MANAGER_FIXTURES_20261013.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["fixtures"]), 3)


if __name__ == "__main__":
    unittest.main()
