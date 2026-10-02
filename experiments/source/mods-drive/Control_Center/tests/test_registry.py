import json
import tempfile
import unittest
from pathlib import Path

from core.installer import LuaComposer
from core.manager import ModuleManager
from core.registry import SettingRegistry


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        module = self.root / "modules" / "test"
        module.mkdir(parents=True)
        (module / "module.json").write_text(json.dumps({"id":"test","name":"Test","version":"1.0.0","author":"qa","type":"lua_table_patch","settings":[{"key":"amount","label":"Amount","type":"slider","min":0,"max":10,"step":0.1,"default":1.5}],"entrypoint":"patch.lua"}))
        (module / "patch.lua").write_text("return {}\n")
        (self.root / "research").mkdir()
        (self.root / "research" / "kfc_candidates_2026-09-24.json").write_text('[{"status":"Research Only","label":"candidate"}]')
        self.manager = ModuleManager(self.root)
        self.registry = SettingRegistry(self.root, self.manager)

    def test_schema_and_migration_preserve_legacy_value(self):
        defs = self.registry.definitions()
        self.assertEqual(defs[0].id, "test.amount")
        migrated, mapping = self.registry.migrate_profile({"module_settings":{"test":{"amount":2.3}},"enabled_modules":{"test":True}})
        self.assertEqual(migrated["module_settings"]["test"]["amount"], 2.3)
        self.assertIn("test.amount", mapping)

    def test_deterministic_composer(self):
        a = LuaComposer(self.root).compose(self.manager.modules, self.manager.active_config)
        b = LuaComposer(self.root).compose(self.manager.modules, self.manager.active_config)
        self.assertEqual(a, b)

    def test_research_is_fail_closed(self):
        self.assertTrue(self.registry.research())
        self.assertTrue(all(item["status"] == "Research Only" for item in self.registry.research()))

    def test_effect_category_and_search(self):
        definition = self.registry.definitions()[0]
        self.assertTrue(definition.category)
        self.assertTrue(definition.subcategory)
        self.assertIn(definition, self.registry.search(definition.id.split(".", 1)[1]))

    def test_duplicate_target_audit_is_reported(self):
        self.assertIsInstance(self.registry.duplicate_targets(), dict)

    def test_every_setting_has_one_valid_location(self):
        from core.registry import TUNING_CATEGORIES, SUBCATEGORIES
        definitions = self.registry.definitions()
        self.assertEqual(len(definitions), len({d.id for d in definitions}))
        self.assertTrue(all(d.category in TUNING_CATEGORIES for d in definitions))
        self.assertTrue(all(d.category == "Advanced Research" or d.subcategory in SUBCATEGORIES[d.category] for d in definitions))
        inventory = self.registry.inventory_mapping()
        self.assertEqual(len(inventory), len(definitions))
        self.assertEqual(len({row["stable_id"] for row in inventory}), len(definitions))

    def test_search_matches_category_and_subcategory(self):
        self.assertTrue(self.registry.search("advanced research"))
        self.assertTrue(self.registry.search("survival"))


if __name__ == "__main__":
    unittest.main()
