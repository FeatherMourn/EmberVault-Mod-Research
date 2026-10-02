import unittest
from pathlib import Path


class DistributionTests(unittest.TestCase):
    def test_distribution_metadata_exists(self):
        root = Path(__file__).parents[1]
        self.assertTrue((root / "pyproject.toml").exists())
        self.assertTrue((root / "INSTALL.md").exists())
        self.assertFalse((root / "Control_Center").exists())


if __name__ == "__main__":
    unittest.main()
