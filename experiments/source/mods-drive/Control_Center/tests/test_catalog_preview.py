import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze_catalog_preview import analyze


class CatalogPreviewEvidenceTests(unittest.TestCase):
    def test_extracts_preview_and_ui_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eml.log"
            rows = [
                {"timestamp": "t", "fields": {"message": "[CC-BED-CLONE] CATALOG_PREVIEW_AFTER|iconImage=nil|iconModel=model-guid|iconScene=nil"}},
                {"timestamp": "t", "fields": {"message": "[CC-BED-CLONE] CATALOG_ICON_ASSIGNMENT|guid=texture-guid"}},
                {"timestamp": "t", "fields": {"message": "[CC-BED-CLONE] CATALOG_RENDER_CONTROL|field=iconRenderGlobalScale|ok=true|value=1.25"}},
                {"timestamp": "t", "fields": {"message": "[CC-BED-CLONE] UI_SET_AFTER|entries=9|sets=9"}},
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            result = analyze(path)
        self.assertEqual(result["status"], "evidence_found")
        self.assertEqual(result["preview_fields"]["after"]["iconModel"], "model-guid")
        self.assertEqual(result["ui_set_after"], "entries=9|sets=9")
        self.assertEqual(result["icon_assignment"], "guid=texture-guid")
        self.assertEqual(result["render_control"], "field=iconRenderGlobalScale|ok=true|value=1.25")

    def test_respects_session_byte_range(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eml.log"
            rows = [
                {"timestamp": "t", "fields": {"message": "[CC-BED-CLONE] CATALOG_RENDER_CONTROL|field=first|ok=true"}},
                {"timestamp": "t", "fields": {"message": "[CC-BED-CLONE] CATALOG_RENDER_CONTROL|field=second|ok=true"}},
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            raw = path.read_bytes()
            split = raw.find(b"\n") + 1
            result = analyze(path, 0, split)
        self.assertEqual(result["render_control"], "field=first|ok=true")


if __name__ == "__main__":
    unittest.main()
