import tempfile
import unittest
from pathlib import Path

from src.catalog_store import CatalogStore
from src.probe_catalog_import import import_probe_result


class ProbeCatalogImportTests(unittest.TestCase):
    def test_imports_read_only_probe_records(self):
        record = {"id": "probe:r1", "kind": "eml-resource-type", "identity": {"resource_type": "keen::ItemInfo"},
                  "build_scope": ["synthetic"], "state": "observed", "confidence": "offline-export",
                  "supported_claims": [], "unsupported_claims": ["No runtime claim"], "open_questions": [],
                  "contradictions": [], "evidence": ["fixture.tsv"]}
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            self.assertEqual(import_probe_result(store, {"read_only": True, "runtime_approval": False, "records": [record]}), 1)
            self.assertEqual(len(store.records(kind="eml-resource-type")), 1)
            store.close()

    def test_rejects_runtime_approved_result(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CatalogStore(Path(directory) / "catalog.sqlite")
            with self.assertRaises(ValueError):
                import_probe_result(store, {"read_only": True, "runtime_approval": True, "records": []})
            store.close()


if __name__ == "__main__":
    unittest.main()
