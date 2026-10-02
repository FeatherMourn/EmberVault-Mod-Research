import json
import tempfile
import unittest
from pathlib import Path

from tools.build_metadata_probe_suite import main


class MetadataProbeSuiteTests(unittest.TestCase):
    def test_suite_uses_verified_types_and_records_quarantine(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            policy = root / "policy.json"
            output = root / "suite"
            policy.write_text(json.dumps({
                "target_build": "test-build",
                "verified_types": [{"type": "keen::ItemInfo"}, {"type": "keen::FbUiBundle"}],
                "quarantined_types": [{"type": "keen::TemplateResource"}],
            }), encoding="utf-8")
            import sys
            old = sys.argv
            try:
                sys.argv = ["build_metadata_probe_suite.py", str(policy), str(output)]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = old
            manifest = json.loads((output / "mod.json").read_text(encoding="utf-8"))
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["verified_types"], ["keen::ItemInfo", "keen::FbUiBundle"])
            self.assertEqual(manifest["quarantined_types"], ["keen::TemplateResource"])
            self.assertNotIn("TemplateResource", source)
            self.assertIn("ItemInfo", source)


if __name__ == "__main__":
    unittest.main()
