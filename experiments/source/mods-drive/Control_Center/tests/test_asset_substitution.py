import unittest
import tempfile
from pathlib import Path

from core.asset_substitution import AssetSubstitutionError, AssetSubstitutionPlanner


class AssetSubstitutionTests(unittest.TestCase):
    def test_color_adjustments_are_normalized_but_remain_research_gated(self):
        plan = AssetSubstitutionPlanner().plan(
            1, 2, color_adjustments=[{"target": "frame", "color": "#ab12ef80"}]
        )
        self.assertEqual(plan.color_adjustments, ({"target": "frame", "color": "#AB12EF80"},))
        self.assertEqual(AssetSubstitutionPlanner.manifest_metadata(plan)["color_adjustments"], list(plan.color_adjustments))

    def test_rejects_invalid_color_adjustment(self):
        with self.assertRaisesRegex(AssetSubstitutionError, "#RRGGBB"):
            AssetSubstitutionPlanner().plan(1, 2, color_adjustments=[{"color": "red"}])

    def test_plan_preserves_mechanics_and_gates_resource_graph(self):
        plan = AssetSubstitutionPlanner().plan(
            2940001508, 3987654401,
            [{"field": "visualModel", "resource_guid": "new-model-guid"}],
        )
        self.assertEqual(plan.mechanics_policy, "preserve")
        self.assertEqual(plan.state, "research-only")
        self.assertEqual(plan.substitutions[0]["ownership"], "external-research")
        metadata = AssetSubstitutionPlanner.manifest_metadata(plan)
        self.assertTrue(metadata["requires_resource_graph_validation"])
        self.assertEqual(metadata["resource_dependencies"], ["new-model-guid"])
        self.assertEqual(metadata["metadata_policy_states"][0]["state"], "unverified")
        self.assertTrue(metadata["policy_review_required"])
        self.assertEqual(metadata["promotion_evidence"],
                         ["runtime_verified", "visual_verified", "rollback_verified"])

    def test_rejects_mechanics_replacement_in_visual_plan(self):
        with self.assertRaises(AssetSubstitutionError):
            AssetSubstitutionPlanner().plan(1, 2, preserve_mechanics=False)

    def test_rejects_donor_overwrite(self):
        with self.assertRaisesRegex(AssetSubstitutionError, "distinct new item ID"):
            AssetSubstitutionPlanner().plan(7, 7)

    def test_rejects_unknown_visual_field(self):
        with self.assertRaises(AssetSubstitutionError):
            AssetSubstitutionPlanner().plan(1, 2, [{"field": "aiBrain"}])

    def test_rejects_duplicate_visual_fields(self):
        with self.assertRaises(AssetSubstitutionError):
            AssetSubstitutionPlanner().plan(
                1, 2,
                [{"field": "visualModel", "resource_guid": "a"},
                 {"field": "visualModel", "resource_guid": "b"}],
            )

    def test_rejects_noop_visual_resource_replacement(self):
        with self.assertRaisesRegex(AssetSubstitutionError, "no-op visual substitution"):
            AssetSubstitutionPlanner().plan(
                1, 2,
                [{"field": "visualModel", "resource_guid": "same", "donor_resource_guid": "same"}],
            )

    def test_rejects_unknown_ownership(self):
        with self.assertRaises(AssetSubstitutionError):
            AssetSubstitutionPlanner().plan(
                1, 2,
                [{"field": "texture", "resource_guid": "x", "ownership": "unknown"}],
            )

    def test_dependency_validation_reports_unavailable_resources(self):
        planner = AssetSubstitutionPlanner()
        plan = planner.plan(1, 2, [{"field": "visualModel", "resource_guid": "model-a"}])
        self.assertEqual(planner.validate_dependencies(plan, {"model-b"}),
                         ["Missing visual resource dependency: model-a"])
        self.assertEqual(planner.validate_dependencies(plan, {"model-a"}), [])
        self.assertTrue(planner.validate_dependencies(plan))

    def test_project_dependency_validation_uses_recorded_resource_ids(self):
        planner = AssetSubstitutionPlanner()
        plan = planner.plan(1, 2, [{"field": "iconImage", "resource_guid": "icon-guid"}])
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "assets.json").write_text(
                '{"schema":"control_center.assets.v1","assets":[],'
                '"references":[{"resource_id":"icon-guid"}]}', encoding="utf-8")
            self.assertEqual(planner.validate_project_dependencies(plan, project), [])

    def test_plan_preserves_optional_asset_reference_metadata(self):
        plan = AssetSubstitutionPlanner().plan(1, 2, [{
            "field": "visualModel", "resource_guid": "model-guid",
            "asset": "assets/models/bed.gltf", "resource_type": "keen::RenderModel",
        }])
        self.assertEqual(plan.substitutions[0]["asset"], "assets/models/bed.gltf")
        self.assertEqual(plan.substitutions[0]["resource_type"], "keen::RenderModel")

    def test_plan_marks_quarantined_resource_types(self):
        plan = AssetSubstitutionPlanner().plan(1, 2, [{
            "field": "visualModel", "resource_guid": "template-guid",
            "resource_type": "keen::TemplateResource",
        }])
        self.assertEqual(plan.substitutions[0]["metadata_policy"]["state"], "quarantined")
        self.assertTrue(AssetSubstitutionPlanner.manifest_metadata(plan)["policy_review_required"])

    def test_project_dependency_validation_checks_declared_resource_type(self):
        planner = AssetSubstitutionPlanner()
        plan = planner.plan(1, 2, [{
            "field": "visualModel", "resource_guid": "model-guid",
            "resource_type": "keen::RenderModel",
        }])
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "assets.json").write_text(
                '{"schema":"control_center.assets.v1","assets":[],'
                '"references":[{"resource_id":"model-guid","resource_type":"keen::ItemInfo"}]}', encoding="utf-8")
            issues = planner.validate_project_dependencies(plan, project)
            self.assertTrue(any("Resource type mismatch" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
