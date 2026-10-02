import json
import tempfile
import unittest
from pathlib import Path

from core.asset_service import AssetService
from core.publication import PublicationPlanner


class PublicationPlannerTests(unittest.TestCase):
    def test_plan_is_build_targeted_and_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            (project / "mod.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "content": [{"id": "demo:item", "path": "content/item.json"}],
            }), encoding="utf-8")
            (project / "content").mkdir()
            (project / "content" / "item.json").write_text("{}", encoding="utf-8")
            source = root / "icon.png"
            source.write_bytes(b"icon")
            AssetService().import_file(source, project, "icons")
            plan_a = PublicationPlanner().plan(project, "1076226")
            plan_b = PublicationPlanner().plan(project, "1076226")
            self.assertTrue(plan_a.publishable)
            self.assertEqual(plan_a.project_fingerprint, plan_b.project_fingerprint)
            self.assertEqual(plan_a.target_build, "1076226")
            self.assertTrue(any(node.kind == "content_asset" for node in plan_a.nodes))

    def test_unresolved_asset_reference_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            (project / "mod.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "content": [{"id": "demo:item", "path": "content/item.json"}],
            }), encoding="utf-8")
            (project / "content").mkdir()
            (project / "content" / "item.json").write_text("{}", encoding="utf-8")
            source = root / "icon.png"
            source.write_bytes(b"icon")
            destination = AssetService().import_file(source, project, "icons")
            AssetService().register_reference(project, destination, "keen::ItemInfo", "iconModel")
            plan = PublicationPlanner().plan(project, "1076226")
            self.assertFalse(plan.publishable)
            self.assertTrue(any("reference_unresolved" in issue for issue in plan.issues))

    def test_missing_resource_is_not_publishable(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            (project / "mod.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "content": [{"id": "demo:item", "path": "content/missing.json"}],
            }), encoding="utf-8")
            plan = PublicationPlanner().plan(project, "1076226")
            self.assertFalse(plan.publishable)
            self.assertTrue(any(node.status == "invalid" for node in plan.nodes))

    def test_declared_asset_dependency_must_have_recorded_reference(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            (project / "mod.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "asset_dependencies": ["model-guid"],
            }), encoding="utf-8")
            plan = PublicationPlanner().plan(project, "1076226")
            self.assertFalse(plan.publishable)
            self.assertTrue(any("dependency_unresolved" in issue for issue in plan.issues))


if __name__ == "__main__":
    unittest.main()
