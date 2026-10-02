import tempfile
import unittest
import json
from pathlib import Path
from tools.verify_authoring_templates import verify
class AuthoringTemplateVerifierTests(unittest.TestCase):
    def test_shipped_templates_are_valid(self):
        result=verify(Path(__file__).resolve().parents[1]/"research"/"templates")
        self.assertTrue(result["valid"], result); self.assertEqual(result["checked"], result["required"])
    def test_missing_template_fails_closed(self):
        with tempfile.TemporaryDirectory() as td: self.assertFalse(verify(Path(td))["valid"])

    def test_interaction_template_safety_fields_are_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shipped = Path(__file__).resolve().parents[1] / "research" / "templates"
            for path in shipped.iterdir():
                (root / path.name).write_bytes(path.read_bytes())
            target = root / "interaction_donor_probe_template.json"
            import json
            data = json.loads(target.read_text(encoding="utf-8"))
            data["runtime_mutation"] = True
            target.write_text(json.dumps(data), encoding="utf-8")
            result = verify(root)
            self.assertFalse(result["valid"])
            self.assertIn("unsafe interaction template field: runtime_mutation", result["errors"])

    def test_visual_variant_rejects_malformed_transform(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shipped = Path(__file__).resolve().parents[1] / "research" / "templates"
            for path in shipped.iterdir():
                (root / path.name).write_bytes(path.read_bytes())
            target = root / "visual_variant_template.json"
            import json
            data = json.loads(target.read_text(encoding="utf-8"))
            data["scale"] = [1, 2]
            target.write_text(json.dumps(data), encoding="utf-8")
            result = verify(root)
            self.assertFalse(result["valid"])
            self.assertIn("visual variant scale must contain exactly three numeric values", result["errors"])

    def test_visual_variant_rejects_unresolved_color_entry(self):
        root = Path(__file__).parents[1] / "research" / "templates"
        target = root / "visual_variant_template.json"
        original = target.read_text(encoding="utf-8")
        try:
            data = json.loads(original)
            data["color_adjustments"] = [{"target": "material", "color": "not-a-color"}]
            target.write_text(json.dumps(data), encoding="utf-8")
            result = verify(root)
            self.assertIn("requires #RRGGBB or #RRGGBBAA color", " ".join(result["errors"]))
        finally:
            target.write_text(original, encoding="utf-8")
if __name__ == "__main__": unittest.main()
