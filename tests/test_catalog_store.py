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
            store.close()


if __name__ == "__main__":
    unittest.main()
