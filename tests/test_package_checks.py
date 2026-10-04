import unittest
import json
from embervault_sdk import validate_manifest
from pathlib import Path

from src.package_checks import verify_package_contents


class PackageChecksTests(unittest.TestCase):
    def test_required_release_files_are_present(self):
        self.assertEqual(verify_package_contents(Path(__file__).parents[1]), [])

    def test_research_artifacts_are_reopenable_and_schema_tagged(self):
        root = Path(__file__).parents[1]
        queue = json.loads((root / "research/REVIEW_QUEUE_20261004.json").read_text())
        publication = json.loads((root / "research/publication/web-catalog-publication-20261004.json").read_text())
        self.assertEqual(queue["schema_version"], 1)
        self.assertEqual(publication["schema_version"], 1)
        self.assertEqual(publication["publication"], "web-catalog")

    def test_publication_snapshot_verifier_is_available(self):
        self.assertTrue((Path(__file__).parents[1] / "tools/verify_publication_snapshot.py").is_file())

    def test_manifest_matches_shared_sdk_contract(self):
        root = Path(__file__).parents[1]
        manifest = json.loads((root / "module.json").read_text())
        self.assertEqual(validate_manifest(manifest), [])
        self.assertTrue(manifest["safety"]["read_only"])
        self.assertEqual(manifest["safety"]["allowed_profiles"], ["research"])


if __name__ == "__main__":
    unittest.main()
