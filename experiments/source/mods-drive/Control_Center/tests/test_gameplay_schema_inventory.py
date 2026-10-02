import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.verify_gameplay_schema_inventory import verify


class GameplaySchemaInventoryTests(unittest.TestCase):
    def test_current_inventory_is_read_only_and_complete(self):
        path = Path(__file__).parents[1] / "research" / "GAMEPLAY_SCHEMA_INVENTORY_1076226.json"
        self.assertEqual(verify(path, "1076226"), [])

    def test_mutation_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            data = {
                "schema": "control_center.gameplay_schema_inventory.v1",
                "build": "1076226",
                "groups": [{"area": area, "runtime_mutation": False, "status": "research-only", "authority": "unknown"}
                           for area in ("interaction", "ai", "quest", "animation", "world_generation", "multiplayer_authority")],
            }
            data["groups"][0]["runtime_mutation"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertIn("interaction: runtime_mutation must be false", verify(path, "1076226"))

    def test_builder_accepts_explicit_current_build_sources(self):
        root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(root / "tools" / "build_gameplay_schema_inventory.py"),
                 "--reflection", r"H:\SteamLibrary\steamapps\common\Enshrouded\.cache\types.json",
                 "--kfc-root", r"H:\ENSHROUDED KFC FILES", "--output-dir", directory],
                cwd=root, capture_output=True, text=True, check=True,
            )
            self.assertIn("gameplay_schema_inventory.v1", result.stdout)
            self.assertTrue((Path(directory) / "GAMEPLAY_SCHEMA_INVENTORY_1076226.json").exists())


if __name__ == "__main__":
    unittest.main()
