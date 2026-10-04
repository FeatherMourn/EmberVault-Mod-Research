import unittest
from pathlib import Path

from src.package_checks import verify_package_contents


class PackageChecksTests(unittest.TestCase):
    def test_required_release_files_are_present(self):
        self.assertEqual(verify_package_contents(Path(__file__).parents[1]), [])


if __name__ == "__main__":
    unittest.main()
