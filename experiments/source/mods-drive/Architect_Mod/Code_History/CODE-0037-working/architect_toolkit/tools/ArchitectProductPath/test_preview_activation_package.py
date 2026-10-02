import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "runtime" / "staging" / "architect_product_path_preview_test"
TARGET = ROOT.parent / "architect_product_path_preview_test"
CANARY_IDS = (3552148149, 2561652817, 1892633990, 2330891540)
ORIGINAL_MOD_SHA = "E6DEF72A6CFA23DF5A52B8F7F1FAA2E7B4C5D7E7ECE9E6CEA571BD96772110D4"
ORIGINAL_STAGING_SHA = "0E4F0E9823087EC0C98225928382F5DDA040E58169BDCAD9127C7C2F78E84575"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PreviewActivationPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod_json = TARGET / "mod.json"
        cls.test_lua = TARGET / "src" / "mod.lua"
        cls.archive_lua = ARCHIVE / "src" / "mod.lua"
        cls.original_lua = ROOT / "src" / "mod.lua"
        cls.original_staging = ROOT / "runtime" / "staging" / "ArchitectProductPathPreview.lua"

    def test_test_mod_is_distinct_and_capabilities_match(self):
        value = json.loads(self.mod_json.read_text(encoding="utf-8"))
        current = json.loads((ROOT / "mod.json").read_text(encoding="utf-8"))
        self.assertEqual(value["id"], "architect_product_path_preview_test")
        self.assertNotEqual(value["id"], current["id"])
        self.assertEqual(value["capabilities"], current["capabilities"])

    def test_original_sources_are_unchanged_and_copy_is_exact(self):
        self.assertEqual(sha(self.original_lua), ORIGINAL_MOD_SHA)
        self.assertEqual(sha(self.original_staging), ORIGINAL_STAGING_SHA)
        self.assertEqual(self.test_lua.read_bytes(), self.archive_lua.read_bytes())

    def test_test_copy_gate_and_banner_are_active(self):
        text = self.test_lua.read_text(encoding="utf-8")
        self.assertIn('enabled = true', text)
        self.assertIn('codeId = "CODE-0014"', text)
        self.assertIn("CODE-0014 ACTIVE", text)
        self.assertIn("preview-only, do not place canaries", text)

    def test_ids_are_unique_and_appear_once_in_mapping(self):
        text = self.test_lua.read_text(encoding="utf-8")
        for item_id in CANARY_IDS:
            self.assertEqual(text.count(str(item_id)), 1)

    def test_no_placement_api_or_payload_overrun(self):
        text = self.test_lua.read_text(encoding="utf-8")
        self.assertNotIn("BuildingPlaceEvent", text)
        self.assertNotIn("place(", text.lower())
        self.assertEqual(text.count("maxPayloadBytes = 8"), 1)
        self.assertNotIn("WriteProcessMemory", text)


if __name__ == "__main__":
    unittest.main()

