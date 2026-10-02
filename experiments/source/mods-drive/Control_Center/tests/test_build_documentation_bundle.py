import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools.build_documentation_bundle import build
from tools.audit_documentation import REQUIRED


class DocumentationBundleTests(unittest.TestCase):
    def test_bundle_contains_all_audited_documents(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for relative in REQUIRED.values():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# documentation\n", encoding="utf-8")
            output = build(root, root / "docs.zip")
            with ZipFile(output) as archive:
                self.assertEqual(sorted(archive.namelist()), sorted(REQUIRED.values()))


if __name__ == "__main__":
    unittest.main()
