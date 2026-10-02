import tempfile, unittest
from pathlib import Path
from tools.verify_installer_source import verify
class InstallerSourceTests(unittest.TestCase):
    def test_current_source_references_required_docs(self):
        root=Path(__file__).resolve().parents[1]; result=verify(root/"packaging/EnshroudedModHub.iss"); self.assertTrue(result["valid"]); self.assertIn("CURRENT_SOURCE_RELEASE_VERIFICATION_20260929.md", result.get("required", []))
    def test_missing_reference_fails(self):
        with tempfile.TemporaryDirectory() as td: self.assertFalse(verify(Path(td)/"missing.iss")["valid"])
