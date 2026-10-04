import tempfile
import unittest
from pathlib import Path

from src.catalog_store import CatalogStore
from src.research_index import load_candidates


class CatalogStoreTests(unittest.TestCase):
    def test_seed_records_migrate_into_durable_store(self):
        source = load_candidates(Path(__file__).parents[1] / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            self.assertEqual(store.import_records(source), 8)
            self.assertEqual(len(store.records()), 8)
            self.assertEqual(len(store.records(kind="recipe-schema")), 1)
            store.close()

    def test_replace_is_atomic_for_same_record_id(self):
        source = load_candidates(Path(__file__).parents[1] / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            store.import_records(source[:1])
            changed = dict(source[0], state="blocked")
            store.import_records([changed])
            self.assertEqual(store.records()[0]["state"], "blocked")
            self.assertEqual(len(store.records()[0]["evidence"]), len(source[0]["evidence"]))
            store.close()

    def test_supplemental_canonical_findings_import(self):
        source = load_candidates(Path(__file__).parents[1] / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
        supplemental = __import__("json").loads((Path(__file__).parents[1] / "research/catalog_records_20261004.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            store.import_records(source)
            store.import_records(supplemental["records"])
            self.assertEqual(len(store.records()), 12)
            self.assertEqual(len(store.records(kind="package-validation")), 1)
            store.close()

    def test_broader_render_model_and_donor_import(self):
        imported = __import__("json").loads((Path(__file__).parents[1] / "research/catalog_records_import_20261004.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            self.assertEqual(store.import_records(imported["records"]), 3)
            self.assertEqual(len(store.records(kind="rendermodel-runtime-evidence")), 1)
            self.assertEqual(len(store.records(kind="donor-probe-contract")), 1)
            store.close()

    def test_kfc_blender_and_recipe_followup_import(self):
        imported = __import__("json").loads((Path(__file__).parents[1] / "research/catalog_records_import_20261004_b.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            self.assertEqual(store.import_records(imported["records"]), 4)
            self.assertEqual(len(store.records(kind="blender-capability-map")), 1)
            self.assertEqual(len(store.records(kind="recipe-workshop-requirements")), 1)
            store.close()

    def test_full_icon_probe_import_is_distinct(self):
        imported = __import__("json").loads((Path(__file__).parents[1] / "research/catalog_records_import_20261004_c.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            self.assertEqual(store.import_records(imported["records"]), 1)
            self.assertEqual(store.records(kind="rendermodel-donor-probe")[0]["state"], "partially-verified")
            store.close()

    def test_contradiction_requires_explicit_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            source = load_candidates(Path(__file__).parents[1] / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
            store.import_records(source[:1])
            contradiction = {"id": "contra-1", "record_id": source[0]["id"], "claim_a": "A", "claim_b": "B", "status": "open"}
            store.add_contradiction(contradiction)
            self.assertEqual(len(store.unresolved_contradictions()), 1)
            with self.assertRaises(ValueError):
                store.resolve_contradiction("contra-1", "resolved", "")
            store.resolve_contradiction("contra-1", "accepted-uncertainty", "Both claims remain build-scoped and unresolved.")
            self.assertEqual(store.unresolved_contradictions(), [])
            self.assertEqual(len(store.all_contradictions()), 1)
            store.close()

    def test_catalog_backup_can_be_reopened(self):
        source = load_candidates(Path(__file__).parents[1] / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = CatalogStore(root / "catalog.sqlite")
            store.import_records(source)
            store.backup_to(root / "recovery/catalog.sqlite")
            store.close()
            recovered = CatalogStore(root / "recovery/catalog.sqlite")
            self.assertEqual(len(recovered.records()), 8)
            recovered.close()

    def test_full_catalog_backup_preserves_records_and_contradictions(self):
        root = Path(__file__).parents[1]
        source = load_candidates(root / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
        source += __import__("json").loads((root / "research/catalog_records_20261004.json").read_text())["records"]
        extra = __import__("json").loads((root / "research/catalog_records_import_20261004.json").read_text())["records"]
        extra_b = __import__("json").loads((root / "research/catalog_records_import_20261004_b.json").read_text())["records"]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            store = CatalogStore(base / "catalog.sqlite")
            store.import_records(source + extra + extra_b)
            store.add_contradiction({"id": "recovery-c-1", "record_id": extra_b[2]["id"], "claim_a": "A", "claim_b": "B", "status": "open"})
            self.assertTrue(store.integrity_check())
            store.backup_to(base / "recovery/catalog.sqlite")
            store.close()
            recovered = CatalogStore(base / "recovery/catalog.sqlite")
            integrity = recovered.integrity_check()
            record_count = len(recovered.records())
            contradiction_count = len(recovered.unresolved_contradictions())
            recovered.close()
            self.assertTrue(integrity)
            self.assertEqual(record_count, 19)
            self.assertEqual(contradiction_count, 1)


if __name__ == "__main__":
    unittest.main()
