import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "runtime" / "admin_action_registry.json"
MODULE = ROOT / "runtime" / "AdminActionRegistry.psm1"


class AdminActionRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.ids = [a["commandId"] for a in cls.raw["actions"]]
        for family in cls.raw["actionFamilies"]:
            cls.ids.extend(family["commandIds"])

    def test_schema_build_categories_and_unique_ids(self):
        self.assertEqual(self.raw["schema"], "architect.admin_action_registry.v2")
        self.assertEqual(self.raw["targetBuild"], 1076226)
        self.assertEqual(len(self.ids), len(set(self.ids)))
        self.assertEqual(self.raw["categories"], [
            "Dashboard", "Player", "Movement & Travel", "Inventory & Items",
            "Crafting & Progression", "World & Game Settings", "Camera & Glider",
            "Combat & Enemy AI", "Building Admin", "Multiplayer Admin", "Inspector / Diagnostics"
        ])

    def test_all_legacy_command_ids_are_preserved(self):
        text = (ROOT / "runtime" / "ArchitectRuntime.ps1").read_text(encoding="utf-8-sig")
        start = text.index("$adminCommandRegistry = @(")
        end = text.index("\n)\n\n# Enrich", start)
        import re
        legacy = set(re.findall(r'action = "([^"]+)"', text[start:end]))
        scaffold_start = text.index("$multiplayerCommandScaffold = @(")
        scaffold_end = text.index("\n)\nforeach ($row", scaffold_start)
        legacy.update(re.findall(r'@\("([^"]+)"', text[scaffold_start:scaffold_end]))
        self.assertEqual(set(), legacy - set(self.ids))

    def test_capability_catalog_covers_requested_settings(self):
        required = {
            "gamesettings.player_health_multiplier", "gamesettings.body_heat",
            "gamesettings.breath_time", "gamesettings.shroud_time",
            "gamesettings.food_timing", "gamesettings.mining_damage",
            "gamesettings.plant_growth", "gamesettings.resource_amount",
            "gamesettings.production_time", "gamesettings.durability",
            "progression.combat_xp", "gamesettings.enemy_perception",
            "gamesettings.enemy_attack_frequency", "gamesettings.boss_health",
            "gamesettings.day_length", "world.time_of_day",
            "crafting.requirements", "crafting.recipe_unlock", "spell.cast_time",
            "world.fog", "world.fast_travel_rules", "glider.speed",
            "building.area_size", "building.restrictions"
        }
        self.assertEqual(set(), required - set(self.ids))

    def test_unproven_families_are_fail_closed(self):
        self.assertTrue(all(f["status"] in {"UNSOLVED", "PLANNED", "EXPERIMENTAL"}
                            for f in self.raw["actionFamilies"]))
        self.assertTrue(all(not a["enabled"] or a["evidenceStatus"] == "PROVEN_BUILD_1076226"
                            for a in self.raw["actions"]))

    def test_preset_mutations_are_disabled(self):
        self.assertEqual({"vanilla", "creative_builder", "explorer", "relaxed_survival", "developer_test"},
                         {p["id"] for p in self.raw["presets"]})
        self.assertTrue(all(not p["enabled"] for p in self.raw["presets"]))

    def test_powershell_loader_expands_and_rejects_missing_handlers(self):
        escaped_module = str(MODULE).replace("'", "''")
        escaped_catalog = str(CATALOG).replace("'", "''")
        script = (
            f"Import-Module '{escaped_module}' -Force; "
            f"$r=Import-AdminActionRegistry -LiteralPath '{escaped_catalog}'; "
            "$a=New-AdminAdapterTable; "
            "$x=Invoke-RegisteredAdminAction -Registry $r -Adapters $a -CommandId 'player.inspect'; "
            "[pscustomobject]@{count=$r.actions.Count;state=$x.state;families=($null -ne $r.actionFamilies)}|ConvertTo-Json -Compress"
        )
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout.strip())
        self.assertGreaterEqual(value["count"], 100)
        self.assertEqual(value["state"], "HANDLER_UNAVAILABLE")
        self.assertFalse(value["families"])

    def test_runtime_uses_registry_for_rendering_and_command_membership(self):
        text = (ROOT / "runtime" / "ArchitectRuntime.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('Import-AdminActionRegistry -LiteralPath $adminActionRegistryFile', text)
        self.assertIn('function Show-AdminPage', text)
        self.assertIn('function Invoke-AdminBackendAdapter', text)
        self.assertIn('Show-AdminPage', text)
        self.assertIn('function Get-AdminCommandDefinition', text)
        self.assertNotIn("-match '^(player|item|movement|travel|world|progression|multiplayer|diagnostics)\\.'", text)

    def test_f7_and_f8_remain_separate(self):
        text = (ROOT / "runtime" / "ArchitectRuntime.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('$VK_F7 = 0x76', text)
        self.assertIn('$VK_F8 = 0x77', text)
        self.assertIn('# F7 is a separate form and never changes F8 controls, selection, or tabs.', text)
        self.assertIn('$hudCategories = @("BUILD", "CREATE", "DESIGN", "ENVIRONMENT", "PROJECT", "BLUEPRINTS", "STUDY")', text)


if __name__ == "__main__":
    unittest.main()
