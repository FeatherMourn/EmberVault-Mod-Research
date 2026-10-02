import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from core.builder_catalog import BuilderCatalog, CatalogItem


class BuilderCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = BuilderCatalog([
            CatalogItem(1, "Palm Bed", "Beds", {"wood": 6, "nails": 4}, ("bed", "comfort")),
            CatalogItem(2, "Stone Bench", "Benches", {"stone": 8}, ("seat",)),
        ])

    def test_search_filters_category_and_tags(self):
        result = self.catalog.search("bed", "Beds", {"comfort"})
        self.assertEqual([item.item_id for item in result], [1])

    def test_recommendations_prioritize_category_tags_and_favorites(self):
        self.catalog.set_favorite(1)
        result = self.catalog.recommend(category="Beds", tags={"bed"})
        self.assertEqual([item.item_id for item in result], [1])

    def test_recommendations_reject_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.catalog.recommend(limit=0)

    def test_recommendations_support_unfiltered_browse(self):
        self.assertEqual([item.item_id for item in self.catalog.recommend(limit=2)], [1, 2])

    def test_material_totals(self):
        self.assertEqual(BuilderCatalog.material_totals(self.catalog.items, 2),
                         {"nails": 8, "stone": 16, "wood": 12})

    def test_metadata_makes_no_runtime_claim(self):
        self.assertFalse(BuilderCatalog.manifest_metadata()["runtime_mutation"])

    def test_favorites_are_catalog_scoped(self):
        self.catalog.set_favorite(1)
        self.assertEqual([item.name for item in self.catalog.favorite_items()], ["Palm Bed"])
        self.catalog.set_favorite(1, False)
        self.assertEqual(self.catalog.favorite_items(), [])
        with self.assertRaises(KeyError):
            self.catalog.set_favorite(999)

    def test_favorites_round_trip_and_drop_removed_items(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "favorites.json"
            self.catalog.set_favorite(1)
            path.write_text(json.dumps({"favorite_item_ids": [1, 999]}), encoding="utf-8")
            self.catalog.load_favorites(path)
            self.assertEqual([item.item_id for item in self.catalog.favorite_items()], [1])
            self.catalog.save_favorites(path)
            saved = json.loads(path.read_text())
            self.assertEqual(saved["favorite_item_ids"], [1])
            self.assertEqual(saved["schema_version"], 1)
            self.assertFalse(path.with_suffix(path.suffix + ".tmp").exists())

    def test_build_plan_calculates_materials_offline(self):
        plan = self.catalog.build_plan("Castle bedroom", {1: 2, 2: 1})
        self.assertEqual(plan.materials(self.catalog),
                         {"nails": 8, "stone": 8, "wood": 12})
        restored = type(plan).from_dict(plan.to_dict())
        self.assertEqual(restored.item_quantities, {1: 2, 2: 1})
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "plan.json"
            self.catalog.save_build_plan(plan, path)
            self.assertEqual(self.catalog.load_build_plan(path).name, "Castle bedroom")

    def test_build_plan_reports_material_shortages_offline(self):
        plan = self.catalog.build_plan("Castle bedroom", {1: 2, 2: 1})
        self.assertEqual(plan.shortages(self.catalog, {"wood": 20, "nails": 3, "stone": 8}),
                         {"nails": 5})
        with self.assertRaises(ValueError):
            plan.shortages(self.catalog, {"wood": -1})

    def test_build_plan_rejects_boolean_quantities(self):
        with self.assertRaises(ValueError):
            self.catalog.build_plan("Invalid", {1: True})
        with self.assertRaises(ValueError):
            type(self.catalog.build_plan("Valid", {1: 1})).from_dict(
                {"name": "Invalid", "item_quantities": {"1": True}}
            )

    def test_build_plan_exposes_resolved_item_breakdown(self):
        plan = self.catalog.build_plan("Castle bedroom", {1: 2, 2: 1})
        self.assertEqual(plan.item_breakdown(self.catalog), [
            {"item_id": 1, "name": "Palm Bed", "category": "Beds", "quantity": 2,
             "materials": {"nails": 8, "wood": 12}},
            {"item_id": 2, "name": "Stone Bench", "category": "Benches", "quantity": 1,
             "materials": {"stone": 8}},
        ])

    def test_imports_registry_records_conservatively(self):
        catalog = BuilderCatalog.from_records([
            {"id": 9, "name": "Castle Gate", "category": "Building",
             "resources": {"stone": 12}, "tags": ["castle"]},
            {"id": "bad", "name": "Ignored"},
        ])
        self.assertEqual(catalog.items[0].name, "Castle Gate")
        self.assertEqual(catalog.items[0].ingredients, {"stone": 12})

    def test_import_rejects_duplicate_ids_and_invalid_ingredient_values(self):
        catalog = BuilderCatalog.from_records([
            {"id": 9, "name": "First", "resources": {"stone": 12, "bad_decimal": 1.5, "negative": -2, "flag": True}},
            {"id": 9, "name": "Duplicate"},
            {"id": 0, "name": "Invalid"},
        ])
        self.assertEqual(len(catalog.items), 1)
        self.assertEqual(catalog.items[0].ingredients, {"stone": 12})

    def test_imports_items_array_from_json(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "catalog.json"
            path.write_text(json.dumps({"items": [{"id": 4, "name": "Wall"}]}), encoding="utf-8")
            self.assertEqual(BuilderCatalog.from_json_file(path).items[0].item_id, 4)

    def test_discovers_local_control_center_projects_without_runtime_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "projects" / "twilight_bed"
            root.mkdir(parents=True)
            (root / "mod.json").write_text(json.dumps({
                "name": "Twilight Blue Bed",
                "feature_state": "research-only",
                "identity": {"numeric_id": 4242},
            }), encoding="utf-8")
            (root.parent / "broken" ).mkdir()
            (root.parent / "broken" / "mod.json").write_text("not json", encoding="utf-8")
            discovered = BuilderCatalog.discover_control_center_projects(root.parent)
            catalog = BuilderCatalog(self.catalog.items)
            self.assertEqual(catalog.add_items(discovered), 1)
            self.assertEqual(catalog.items[-1].name, "Twilight Blue Bed")
            self.assertIn("research-only", catalog.items[-1].tags)
            self.assertEqual(catalog.add_items(discovered), 0)

    def test_build_plan_report_cli_is_offline_and_machine_readable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = root / "catalog.json"
            plan = root / "plan.json"
            inventory = root / "inventory.json"
            catalog.write_text(json.dumps({"items": [{"id": 1, "name": "Wall", "resources": {"stone": 4}}]}), encoding="utf-8")
            plan.write_text(json.dumps({"name": "Keep", "item_quantities": {"1": 2}}), encoding="utf-8")
            inventory.write_text(json.dumps({"stone": 3}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/report_build_plan.py", str(catalog), str(plan), "--inventory", str(inventory)],
                capture_output=True, text=True, cwd=Path(__file__).parents[1], check=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["shortages"], {"stone": 5})
            self.assertEqual(report["items"][0]["name"], "Wall")
            self.assertFalse(report["runtime_mutation"])


if __name__ == "__main__":
    unittest.main()
