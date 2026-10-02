import json
import tempfile
import unittest
from pathlib import Path

from research.tools.verify_icon_import_log import verify


class IconImportVerifierTests(unittest.TestCase):
    prefix = "[CC-COMBINED-LOCALIZED-BED] "

    def _write(self, records):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "eml.log"
        path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return tmp, path

    def test_complete_runtime_evidence_is_valid(self):
        tmp, path = self._write([
            {"fields": {"message": self.prefix + "IMPORTED_ICON|ok=true|result=f91877f0-7248-7a43-8d8c-6e9c89a53ba4"}},
            {"fields": {"message": self.prefix + "REGISTERED|itemId=3987654333|recipeId=3987654334"}},
            {"fields": {"message": self.prefix + "UI_LINKS|1|matching_sets=1"}},
        ])
        try:
            report = verify(path, self.prefix)
        finally:
            tmp.cleanup()
        self.assertTrue(report["valid"])
        self.assertEqual(report["missing"], [])

    def test_partial_evidence_is_invalid(self):
        tmp, path = self._write([
            {"fields": {"message": self.prefix + "IMPORTED_ICON|ok=true|result=f91877f0-7248-7a43-8d8c-6e9c89a53ba4"}},
        ])
        try:
            report = verify(path, self.prefix)
        finally:
            tmp.cleanup()
        self.assertFalse(report["valid"])
        self.assertEqual(set(report["missing"]), {"REGISTERED", "UI_LINKS"})

    def test_malformed_json_is_ignored_without_false_positive(self):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "eml.log"
        path.write_text("not json\n{}\n", encoding="utf-8")
        try:
            report = verify(path, self.prefix)
        finally:
            tmp.cleanup()
        self.assertFalse(report["valid"])
        self.assertEqual(set(report["missing"]), {"IMPORTED_ICON", "REGISTERED", "UI_LINKS"})


if __name__ == "__main__":
    unittest.main()
