import tempfile
import unittest
from pathlib import Path

from src.catalog_store import CatalogStore
from src.research_bundle import create_bundle, recover_bundle, verify_bundle


class ResearchBundleTests(unittest.TestCase):
    def test_bundle_round_trip_is_hash_verified_and_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.sqlite"
            store = CatalogStore(catalog)
            store.close()
            bundle = root / "research.bundle.zip"
            manifest = create_bundle(catalog, bundle)
            self.assertTrue(manifest["read_only"])
            self.assertFalse(manifest["runtime_approval"])
            self.assertEqual(verify_bundle(bundle)["catalog_sha256"], manifest["catalog_sha256"])
            recovered = root / "recovered.sqlite"
            recover_bundle(bundle, recovered)
            self.assertTrue(recovered.exists())

    def test_tampered_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.sqlite"
            store = CatalogStore(catalog); store.close()
            bundle = root / "research.bundle.zip"
            create_bundle(catalog, bundle)
            import zipfile
            with zipfile.ZipFile(bundle, "a") as archive:
                archive.writestr("catalog.sqlite", b"tampered")
            with self.assertRaises(ValueError):
                verify_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
