import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze_fb_ui_structure import analyze


class FbUiStructureEvidenceTests(unittest.TestCase):
    def test_extracts_read_only_typed_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eml.log"
            rows = [
                {"fields": {"message": "[CC-FBUI-STRUCTURE] FIELD|icons|lua_type=userdata"}},
                {"fields": {"message": "[CC-FBUI-STRUCTURE] FIELD|menu.crafting|lua_type=userdata"}},
                {"fields": {"message": "[CC-FBUI-STRUCTURE] BUNDLES|1"}},
                {"fields": {"message": "[CC-FBUI-STRUCTURE] WARNING|read_only_structure_only"}},
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            result = analyze(path)
        self.assertEqual(result["status"], "evidence_found")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["bundles"], 1)
        self.assertEqual(result["fields"]["icons"]["lua_type"], "userdata")


if __name__ == "__main__":
    unittest.main()
