import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_research_cycle import verify


class VerifyResearchCycleTests(unittest.TestCase):
    def test_valid_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); suite = root / "suite"; (suite / "src").mkdir(parents=True)
            (suite / "mod.json").write_text("{}", encoding="utf-8")
            (suite / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            cycle = root / "RESEARCH_CYCLE.json"
            cycle.write_text(json.dumps({"schema": "control_center.research_cycle.v1", "verified_types": ["keen::ItemInfo"], "quarantined_types": ["keen::TemplateResource"], "generated_probe_suite": str(suite)}), encoding="utf-8")
            self.assertTrue(verify(cycle)["valid"])

    def test_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); cycle = root / "RESEARCH_CYCLE.json"
            cycle.write_text(json.dumps({"schema": "control_center.research_cycle.v1", "verified_types": ["keen::ItemInfo"], "quarantined_types": ["keen::ItemInfo"], "generated_probe_suite": str(root)}), encoding="utf-8")
            result = verify(cycle)
            self.assertFalse(result["valid"])
            self.assertIn("overlap", " ".join(result["errors"]))

    def test_staged_probe_is_required_when_declared(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); suite = root / "suite"; (suite / "src").mkdir(parents=True)
            (suite / "mod.json").write_text("{}", encoding="utf-8")
            (suite / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            cycle = root / "RESEARCH_CYCLE.json"
            cycle.write_text(json.dumps({"schema": "control_center.research_cycle.v1", "verified_types": ["Item"], "quarantined_types": [], "generated_probe_suite": str(suite), "staged_probe": "missing"}), encoding="utf-8")
            result = verify(cycle)
            self.assertFalse(result["valid"])
            self.assertIn("staged probe", " ".join(result["errors"]))

    def test_staged_probe_hash_detects_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); suite = root / "suite"; probe = root / "probe"
            (suite / "src").mkdir(parents=True); probe.mkdir()
            (suite / "mod.json").write_text("{}", encoding="utf-8"); (suite / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            (probe / "mod.json").write_text("{\"id\":\"probe\"}", encoding="utf-8")
            cycle = root / "RESEARCH_CYCLE.json"
            cycle.write_text(json.dumps({"schema": "control_center.research_cycle.v1", "verified_types": ["Item"], "quarantined_types": [], "generated_probe_suite": str(suite), "staged_probe": str(probe), "staged_probe_sha256": "wrong"}), encoding="utf-8")
            result = verify(cycle)
            self.assertFalse(result["valid"])
            self.assertIn("integrity hash", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
