import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.content_patch import ContentPatchError, ContentPatchPlanner


class ContentPatchTests(unittest.TestCase):
    def test_verified_patch_is_applied_without_mutating_donor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"; out = root / "out.json"
            donor.write_text(json.dumps({"name": "Old", "iconImage": None}), encoding="utf-8")
            plan = ContentPatchPlanner().plan(donor, out, "keen::ItemInfo", {"name": "New"})
            ContentPatchPlanner().apply_extracted(plan)
            self.assertEqual(json.loads(donor.read_text())["name"], "Old")
            self.assertEqual(json.loads(out.read_text())["name"], "New")
            self.assertTrue(plan.deployable)

    def test_visual_patch_is_blocked_without_research_override(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"
            donor.write_text("{}", encoding="utf-8")
            planner = ContentPatchPlanner()
            plan = planner.plan(
                donor, root / "out.json", "keen::ItemInfo",
                {"color": {"r": 1, "g": 0, "b": 0}},
            )
            self.assertEqual(plan.changes[0].status, "research-only")
            with self.assertRaises(ContentPatchError): planner.apply_extracted(plan)

    def test_unknown_patch_field_is_never_deployable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"; donor.write_text("{}", encoding="utf-8")
            planner = ContentPatchPlanner()
            plan = planner.plan(donor, root / "out.json", "keen::ItemInfo", {"teleportMesh": True})
            self.assertEqual(plan.changes[0].status, "unsupported")
            self.assertFalse(plan.deployable)

    def test_existing_field_type_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"
            donor.write_text(json.dumps({"name": "Old"}), encoding="utf-8")
            plan = ContentPatchPlanner().plan(donor, root / "out.json", "keen::ItemInfo", {"name": 7})
            self.assertEqual(plan.changes[0].status, "unsupported")
            self.assertIn("does not match", plan.changes[0].reason)

    def test_patch_plan_cli_is_review_only_and_returns_deployability(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"; changes = root / "changes.json"
            donor.write_text(json.dumps({"name": "Old"}), encoding="utf-8")
            changes.write_text(json.dumps({"name": "New"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/report_patch_plan.py", str(donor), "keen::ItemInfo", str(changes)],
                cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True,
            )
            report = json.loads(result.stdout)
            self.assertTrue(report["deployable"])
            self.assertFalse(report["runtime_mutation"])
            self.assertFalse((root / "planned-output.json").exists())

    def test_patch_rejects_donor_changes_after_planning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"; out = root / "out.json"
            donor.write_text(json.dumps({"name": "Old"}), encoding="utf-8")
            plan = ContentPatchPlanner().plan(donor, out, "keen::ItemInfo", {"name": "New"})
            donor.write_text(json.dumps({"name": "Changed"}), encoding="utf-8")
            with self.assertRaisesRegex(ContentPatchError, "changed after"):
                ContentPatchPlanner().apply_extracted(plan)

    def test_patch_rejects_in_place_output(self):
        with tempfile.TemporaryDirectory() as td:
            donor = Path(td) / "donor.json"
            donor.write_text(json.dumps({"name": "Old"}), encoding="utf-8")
            with self.assertRaisesRegex(ContentPatchError, "separate from the donor"):
                ContentPatchPlanner().plan(donor, donor, "keen::ItemInfo", {"name": "New"})

    def test_identity_fields_reject_invalid_values(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"
            donor.write_text(json.dumps({"itemId": 123, "name": "Old"}), encoding="utf-8")
            planner = ContentPatchPlanner()
            invalid_id = planner.plan(donor, root / "id.json", "keen::ItemInfo", {"itemId": 0})
            invalid_name = planner.plan(donor, root / "name.json", "keen::ItemInfo", {"name": "   "})
            self.assertEqual(invalid_id.changes[0].status, "unsupported")
            self.assertIn("positive integers", invalid_id.changes[0].reason)
            self.assertEqual(invalid_name.changes[0].status, "unsupported")
            self.assertIn("non-empty text", invalid_name.changes[0].reason)

    def test_color_payload_requires_normalized_channels(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor = root / "donor.json"
            donor.write_text("{}", encoding="utf-8")
            planner = ContentPatchPlanner()
            invalid = planner.plan(
                donor, root / "invalid.json", "keen::ItemInfo",
                {"color": {"r": 255, "g": 0, "b": 0}},
            )
            valid = planner.plan(
                donor, root / "valid.json", "keen::ItemInfo",
                {"color": {"r": 1, "g": 0.25, "b": 0, "a": 1}},
            )
            self.assertEqual(invalid.changes[0].status, "unsupported")
            self.assertIn("normalized 0..1", invalid.changes[0].reason)
            self.assertEqual(valid.changes[0].status, "research-only")


if __name__ == "__main__":
    unittest.main()
