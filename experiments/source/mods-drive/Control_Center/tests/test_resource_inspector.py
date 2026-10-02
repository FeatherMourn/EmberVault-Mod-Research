import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.resource_inspector import ResourceInspector


class ResourceInspectorTests(unittest.TestCase):
    def test_metadata_policy_distinguishes_verified_and_quarantined_types(self):
        inspector = ResourceInspector()
        self.assertEqual(inspector.metadata_policy("keen::ItemInfo")["state"], "verified")
        self.assertEqual(inspector.metadata_policy("ItemInfo")["state"], "verified")
        self.assertEqual(inspector.metadata_policy("keen::TemplateResource")["state"], "quarantined")
        self.assertEqual(inspector.metadata_policy("keen::Unknown")["state"], "unverified")
    def test_inspects_verified_bed_donor(self):
        root = Path(r"I:\My Drive\Enshrouded Mods\Control_Center\research\staging\bed_clone_kfc_subset_1076226\ItemInfo")
        donor_path = next(path for path in root.glob("*.json") if "01474f79" in path.name)
        record = ResourceInspector().inspect(donor_path, "keen::ItemInfo")
        self.assertEqual(record.data["itemId"]["value"], 2940001508)
        self.assertIn("itemId", record.schema)
        self.assertTrue(record.arrays)

    def test_schema_difference_blocks_type_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor_dir = root / "ItemInfo"; donor_dir.mkdir()
            donor = donor_dir / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_0.json"
            candidate = donor_dir / "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb_0.json"
            donor.write_text(json.dumps({"itemId": {"value": 1}, "name": "label", "entries": [1, 2]}), encoding="utf-8")
            candidate.write_text(json.dumps({"itemId": {"value": "wrong"}, "name": "label", "entries": [1]}), encoding="utf-8")
            inspector = ResourceInspector(); plan = inspector.clone_plan(donor, root / "out.json", "keen::ItemInfo", candidate)
            self.assertFalse(plan.safe)
            self.assertTrue(any(item.path == "itemId.value" for item in plan.differences))
            self.assertTrue(any("array" in item.message.lower() for item in plan.differences))

    def test_clone_plan_warns_for_quarantined_metadata_type(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor_dir = root / "TemplateResource"; donor_dir.mkdir()
            donor = donor_dir / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_0.json"
            donor.write_text(json.dumps({"value": 1}), encoding="utf-8")
            plan = ResourceInspector().clone_plan(donor, root / "out.json", "keen::TemplateResource")
            self.assertTrue(any("quarantined" in warning.lower() for warning in plan.warnings))

    def test_scan_skips_manifests_and_finds_resources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "mod.json").write_text("{}", encoding="utf-8")
            folder = root / "ItemInfo"; folder.mkdir(); (folder / "one.json").write_text("{\"x\": 1}", encoding="utf-8")
            records = ResourceInspector().scan(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].resource_type, "ItemInfo")

    def test_visual_references_are_reported_as_research_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_0.json"
            path.write_text(json.dumps({
                "visualModel": "model-guid",
                "icon": {"image": "icon-guid"},
                "stats": {"value": 3},
                "renderEnabled": True,
                "materials": [{"texture": 42}],
            }), encoding="utf-8")
            inspector = ResourceInspector()
            references = inspector.visual_references(inspector.inspect(path, "keen::ItemInfo"))
            paths = {item["path"] for item in references}
            self.assertIn("visualModel", paths)
            self.assertIn("icon.image", paths)
            self.assertIn("materials[0].texture", paths)
            self.assertNotIn("stats.value", paths)

    def test_visual_substitution_plan_classifies_reference_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            donor_path = root / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_0.json"
            candidate_path = root / "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb_0.json"
            donor_path.write_text(json.dumps({"visualModel": "old", "icon": "same"}), encoding="utf-8")
            candidate_path.write_text(json.dumps({"visualModel": "new", "icon": "same", "texture": "extra"}), encoding="utf-8")
            inspector = ResourceInspector()
            donor = inspector.inspect(donor_path, "keen::ItemInfo")
            candidate = inspector.inspect(candidate_path, "keen::ItemInfo")
            states = {item["path"]: item["state"] for item in inspector.visual_substitution_plan(donor, candidate)}
            self.assertEqual(states["visualModel"], "candidate_reference")
            self.assertEqual(states["icon"], "unchanged")
            self.assertEqual(states["texture"], "new_candidate_reference")

    def test_visual_dependency_report_cli_emits_substitution_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            donor = root / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_0.json"
            candidate = root / "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb_0.json"
            donor.write_text(json.dumps({"model": "old-model"}), encoding="utf-8")
            candidate.write_text(json.dumps({"model": "new-model"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/report_visual_dependencies.py", str(donor), "--candidate", str(candidate)],
                cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True,
            )
            report = json.loads(result.stdout)
            self.assertFalse(report["runtime_substitution_verified"])
            self.assertEqual(report["substitution_plan"][0]["state"], "candidate_reference")
            self.assertTrue(report["candidate_graph_complete"])
            self.assertEqual(report["substitution_summary"]["candidate_reference"], 1)
            self.assertEqual(report["schema_differences"], [])

    def test_visual_dependency_report_fails_for_incomplete_candidate_graph(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            donor = root / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_0.json"
            candidate = root / "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb_0.json"
            donor.write_text(json.dumps({"model": "old-model", "texture": "required"}), encoding="utf-8")
            candidate.write_text(json.dumps({"model": "new-model"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/report_visual_dependencies.py", str(donor), "--candidate", str(candidate)],
                cwd=Path(__file__).parents[1], capture_output=True, text=True, check=False,
            )
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(report["candidate_graph_complete"])
            self.assertEqual(report["substitution_summary"]["missing_in_candidate"], 1)
            self.assertTrue(report["schema_differences"])


if __name__ == "__main__":
    unittest.main()
