import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_furniture_clone_runtime_evidence import verify


class FurnitureCloneRuntimeEvidenceTests(unittest.TestCase):
    def _write(self, data):
        td = tempfile.TemporaryDirectory()
        path = Path(td.name) / "evidence.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return td, path

    def test_accepts_clean_partial_registration_report(self):
        td, path = self._write({
            "schema": "control_center.furniture_clone_runtime_evidence.v1",
            "probe": "chair", "game_build": "1076226", "log": "run.log",
            "donor": {"item_id": 1, "recipe_id": 2},
            "clone": {"item_id": 3, "recipe_id": 4},
            "runtime": {"clone_registered": True, "clone_discovered": True,
                         "panic_or_loader_error": False, "item_registry_increment": 1,
                         "recipe_registry_increment": 1, "knowledge_link_increment": 1,
                         "ui_set_clone_increment": 1},
            "cleanup": {"probe_removed": True, "third_party_mod_restored": True,
                         "stable_profile_restored": True},
            "verdict": "partial_runtime_registration",
        })
        self.addCleanup(td.cleanup)
        self.assertTrue(verify(path)["valid"])

    def test_rejects_panic_or_missing_cleanup(self):
        td, path = self._write({"schema": "control_center.furniture_clone_runtime_evidence.v1",
                                "runtime": {"panic_or_loader_error": True},
                                "cleanup": {"probe_removed": False}})
        self.addCleanup(td.cleanup)
        result = verify(path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("panic_or_loader_error" in error for error in result["errors"]))
        self.assertTrue(any("probe_removed" in error for error in result["errors"]))
