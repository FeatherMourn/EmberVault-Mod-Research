import unittest
import json
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


if __name__ == "__main__":
    unittest.main()
