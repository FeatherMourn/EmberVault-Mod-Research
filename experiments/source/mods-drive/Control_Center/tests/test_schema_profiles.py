import tempfile
import unittest
import json
from pathlib import Path

from core.schema_profiles import SchemaProfileService


class SchemaProfileTests(unittest.TestCase):
    def test_snapshot_and_cross_build_diff(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old" / "ItemInfo"; old.mkdir(parents=True)
            new = root / "new" / "ItemInfo"; new.mkdir(parents=True)
            (old / "one.json").write_text('{"itemId":1,"name":"old","requirements":[1]}', encoding="utf-8")
            (new / "one.json").write_text('{"itemId":"1","name":"new","requirements":[1,2],"icon":"x"}', encoding="utf-8")
            service = SchemaProfileService()
            before = service.snapshot(root / "old", "1070000")
            after = service.snapshot(root / "new", "1076226")
            changes = service.compare(before, after)
            self.assertNotEqual(before.fingerprint, after.fingerprint)
            self.assertTrue(any(change.severity == "error" and change.path == "itemId" for change in changes))
            self.assertTrue(any("array length" in change.message for change in changes))
            self.assertTrue(any(change.path == "icon" for change in changes))

    def test_snapshot_write_includes_build_and_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "ItemInfo").mkdir()
            (root / "ItemInfo" / "one.json").write_text('{"itemId":1}', encoding="utf-8")
            destination = root / "snapshot.json"
            snapshot = SchemaProfileService().snapshot(root, "1076226")
            SchemaProfileService.write(snapshot, destination)
            text = destination.read_text(encoding="utf-8")
            self.assertIn('"build_id": "1076226"', text)
            self.assertIn(snapshot.fingerprint, text)

    def test_module_schema_declares_asset_dependencies(self):
        schema = json.loads((Path(__file__).parents[1] / "core" / "module.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["asset_dependencies"]["type"], "array")

    def test_module_schema_separates_loader_capability_and_version(self):
        schema = json.loads((Path(__file__).parents[1] / "core" / "module.schema.json").read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertIn("required_loader_api", properties)
        self.assertIn("required_loader_api_version", properties)
        self.assertIn("pattern", properties["required_loader_api_version"])

    def test_module_schema_requires_maturity_metadata(self):
        schema = json.loads((Path(__file__).parents[1] / "core" / "module.schema.json").read_text(encoding="utf-8"))
        self.assertIn("feature_state", schema["required"])

    def test_module_schema_declares_template_graph_plan(self):
        schema = json.loads(Path("core/module.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["template_graph_plan"]["type"], "object")
        properties = schema["properties"]["template_graph_plan"]["properties"]
        self.assertEqual(properties["source_sha256"]["pattern"], "^[0-9a-f]{64}$")
        self.assertEqual(properties["candidate_sha256"]["pattern"], "^[0-9a-f]{64}$")
        self.assertEqual(properties["component_index"]["minimum"], 0)


if __name__ == "__main__":
    unittest.main()
