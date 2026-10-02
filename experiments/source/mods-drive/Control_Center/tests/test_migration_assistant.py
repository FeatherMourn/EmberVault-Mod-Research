import json
import tempfile
import unittest
from pathlib import Path

from core.migration_assistant import MigrationAssistant
from core.schema_profiles import SchemaProfileService


class MigrationAssistantTests(unittest.TestCase):
    def test_identifies_affected_project_and_action(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old" / "ItemInfo"; old.mkdir(parents=True)
            new = root / "new" / "ItemInfo"; new.mkdir(parents=True)
            (old / "item.json").write_text('{"itemId":1}', encoding="utf-8")
            (new / "item.json").write_text('{"itemId":"1"}', encoding="utf-8")
            project = root / "project"; project.mkdir()
            (project / "mod.json").write_text(json.dumps({"content": [{"resource_type": "keen::ItemInfo"}]}), encoding="utf-8")
            service = SchemaProfileService()
            impacts = MigrationAssistant().analyze(service.snapshot(old.parent, "1"), service.snapshot(new.parent, "2"), [project])
            self.assertEqual(impacts[0].affected_types, ("ItemInfo",))
            self.assertEqual(impacts[0].action, "disable_pending_review")

    def test_unrelated_project_is_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); old = root / "old"; new = root / "new"
            (old / "ItemInfo").mkdir(parents=True); (new / "ItemInfo").mkdir(parents=True)
            (old / "ItemInfo" / "a.json").write_text('{"id":1}', encoding="utf-8")
            (new / "ItemInfo" / "a.json").write_text('{"id":"1"}', encoding="utf-8")
            project = root / "project"; project.mkdir()
            (project / "mod.json").write_text(json.dumps({"content": [{"resource_type": "keen::RecipeRegistryResource"}]}), encoding="utf-8")
            service = SchemaProfileService()
            impacts = MigrationAssistant().analyze(service.snapshot(old, "1"), service.snapshot(new, "2"), [project])
            self.assertEqual(impacts[0].action, "unchanged")


if __name__ == "__main__":
    unittest.main()
