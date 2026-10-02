import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_catalog import build


class CatalogTests(unittest.TestCase):
    def test_catalog_preserves_structural_blueprint_classification(self):
        root = HERE.parents[2]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "build_catalog.json"
            snap = Path(temp) / "snap_rule_catalog.json"
            build(root / "data" / "architect_game_data_1076226.sqlite", out, snap)
            catalog = json.loads(out.read_text(encoding="utf-8"))
            ceiling = next(row for row in catalog["items"] if row["itemId"] == 81726253)
            self.assertEqual(ceiling["classification"], "Voxel Blueprint")
            self.assertTrue(ceiling["registryMembership"])
            self.assertEqual(catalog["backendStatus"], "read_only_catalog")
            self.assertGreaterEqual(catalog["coverageCounts"]["items"], 3609)
            self.assertEqual(catalog["gameBuild"]["sourceBundleSha256"], "153BE9AF6875DB39594FDCAC7A08EE8B316C802BE8A426D24F0A9DFAE713C474")
            self.assertGreater(catalog["coverageCounts"]["buildingMaterialItems"], 0)
            self.assertGreater(catalog["coverageCounts"]["terrainItems"], 0)

    def test_snap_catalog_uses_ingested_rules_when_available(self):
        root = HERE.parents[2]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "build_catalog.json"
            snap = Path(temp) / "snap_rule_catalog.json"
            build(root / "data" / "architect_game_data_1076226.sqlite", out, snap)
            report = json.loads(snap.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "AVAILABLE")
            self.assertEqual(report["configurationCount"], 7)
            self.assertEqual(report["ruleCount"], 31)


if __name__ == "__main__":
    unittest.main()
