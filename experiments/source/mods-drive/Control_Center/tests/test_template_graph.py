import json
import tempfile
import unittest
from pathlib import Path

from core.template_graph import TemplateGraphError, TemplateGraphPlanner


class TemplateGraphPlannerTests(unittest.TestCase):
    def test_plans_model_only_replacement_and_preserves_components(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::Health", "$value": {"max": 10}},
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "donor-guid"}},
            ]}), encoding="utf-8")
            plan = TemplateGraphPlanner().plan(source, "replacement-guid")
            self.assertEqual(plan.component_path, "components[1].$value.model")
            self.assertEqual(plan.donor_model_guid, "donor-guid")
            self.assertTrue(plan.preserved_components)
            metadata = TemplateGraphPlanner.manifest_metadata(plan)
            self.assertEqual(metadata["runtime_mutation"], False)
            self.assertEqual(metadata["component_index"], 1)
            self.assertIn("donor_unchanged", metadata["rollback_policy"])
            self.assertEqual(len(metadata["source_sha256"]), 64)
            self.assertTrue(any("placed object visibly uses" in item for item in metadata["promotion_requirements"]))

    def test_rejects_missing_model_component(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            source.write_text('{"components":[]}', encoding="utf-8")
            with self.assertRaises(TemplateGraphError):
                TemplateGraphPlanner().plan(source, "replacement-guid")

    def test_writes_candidate_without_overwriting_donor(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"; destination = Path(td) / "candidate.json"
            original = {"components": [
                {"$type": "keen::ecs::Health", "$value": {"max": 10}},
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "donor-guid"}},
            ]}
            source.write_text(json.dumps(original), encoding="utf-8")
            plan = TemplateGraphPlanner().plan(source, "replacement-guid")
            TemplateGraphPlanner().write_candidate(plan, destination)
            self.assertEqual(json.loads(source.read_text())["components"][1]["$value"]["model"], "donor-guid")
            candidate = json.loads(destination.read_text())
            self.assertEqual(candidate["components"][1]["$value"]["model"], "replacement-guid")
            self.assertEqual(candidate["components"][0], original["components"][0])
            valid, unexpected = TemplateGraphPlanner.verify_candidate(plan, destination)
            self.assertTrue(valid)
            self.assertEqual(unexpected, ())

    def test_refuses_stale_donor_after_planning(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            candidate = Path(td) / "candidate.json"
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "donor"}},
            ]}), encoding="utf-8")
            plan = TemplateGraphPlanner().plan(source, "replacement")
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "updated-donor"}},
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(TemplateGraphError, "changed after planning"):
                TemplateGraphPlanner().write_candidate(plan, candidate)

    def test_candidate_verification_rejects_unplanned_component_change(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"; candidate = Path(td) / "candidate.json"
            source.write_text('{"components":[{"$type":"keen::ecs::ModelResource","$value":{"model":"donor"}},{"health":10}]}', encoding="utf-8")
            plan = TemplateGraphPlanner().plan(source, "replacement")
            TemplateGraphPlanner().write_candidate(plan, candidate)
            data = json.loads(candidate.read_text()); data["components"][1]["health"] = 99
            candidate.write_text(json.dumps(data), encoding="utf-8")
            valid, unexpected = TemplateGraphPlanner.verify_candidate(plan, candidate)
            self.assertFalse(valid)
            self.assertIn("components[1].health", unexpected)

    def test_rejects_ambiguous_multiple_model_components(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "one"}},
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "two"}},
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(TemplateGraphError, "multiple ModelResource"):
                TemplateGraphPlanner().plan(source, "replacement")

    def test_explicit_model_component_index_allows_multi_model_template(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "one"}},
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "two"}},
            ]}), encoding="utf-8")
            plan = TemplateGraphPlanner().plan(source, "replacement", 1)
            self.assertEqual(plan.component_path, "components[1].$value.model")

    def test_inventory_lists_component_types_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            source.write_text('{"components":[{"$type":"keen::ecs::Health"},{"$type":"keen::ecs::ModelResource"}]}', encoding="utf-8")
            self.assertEqual(TemplateGraphPlanner.inventory(source), (
                {"index": 0, "type": "keen::ecs::Health"},
                {"index": 1, "type": "keen::ecs::ModelResource"},
            ))


if __name__ == "__main__":
    unittest.main()
