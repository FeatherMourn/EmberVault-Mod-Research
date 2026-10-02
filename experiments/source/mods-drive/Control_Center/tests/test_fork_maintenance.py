import tempfile
import unittest
from pathlib import Path

from core.fork_maintenance import ForkMaintenanceService


class ForkMaintenanceTests(unittest.TestCase):
    def test_missing_repository_is_reported_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            status = ForkMaintenanceService().inspect(Path(td) / "missing")
            self.assertIsNone(status.head)
            self.assertTrue(status.issues)

    def test_workspace_crates_are_discovered(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / ".git").mkdir(); (root / "crates" / "mod-loader-lua").mkdir(parents=True)
            (root / "crates" / "mod-loader-lua" / "Cargo.toml").write_text("[package]\nname='x'", encoding="utf-8")
            status = ForkMaintenanceService().inspect(root)
            self.assertEqual(status.workspace_crates, ("mod-loader-lua",))


if __name__ == "__main__":
    unittest.main()
