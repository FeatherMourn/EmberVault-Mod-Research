import tempfile
import unittest
from pathlib import Path

from core.content_project import ContentProjectGenerator
from core.smoke_tests import ContentSmokeTester


class SmokeTests(unittest.TestCase):
    def test_generated_project_passes_smoke_tests(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            project = ContentProjectGenerator(base, Path(td) / "ids.json").create(Path(td) / "project", "smoke_mod", "Smoke Project", "Tester")
            report = ContentSmokeTester().run(project)
            self.assertTrue(report.passed, [check.details for check in report.checks if not check.passed])

    def test_tampered_project_fails_hash_smoke_test(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            project = ContentProjectGenerator(base, Path(td) / "ids.json").create(Path(td) / "project", "smoke_mod", "Smoke Project", "Tester")
            (project / "src" / "mod.lua").write_text("-- tampered", encoding="utf-8")
            report = ContentSmokeTester().run(project)
            self.assertFalse(report.passed)
            self.assertTrue(any(check.name == "package hashes" and not check.passed for check in report.checks))


if __name__ == "__main__":
    unittest.main()
