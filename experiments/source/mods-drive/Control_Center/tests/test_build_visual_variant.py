import json
import tempfile
import unittest
from pathlib import Path

from tools.build_visual_variant import build


class VisualVariantBuilderTests(unittest.TestCase):
    def test_builds_research_only_validated_variant(self):
        template = Path(__file__).parents[1] / "research" / "templates" / "visual_variant_template.json"
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            data = json.loads(template.read_text(encoding="utf-8"))
            data["replacement_model_guid"] = "new-model"
            data["color_adjustments"] = [{"target": "frame", "color": "#AABBCC"}]
            source.write_text(json.dumps(data), encoding="utf-8")
            output = Path(td) / "variant.json"
            result = build(source, output, 3987654999)
            self.assertEqual(result["feature_state"], "research-only")
            self.assertEqual(result["new_item_id"], 3987654999)
            self.assertTrue(result["validated_plan"]["requires_resource_graph_validation"])
            self.assertEqual(json.loads(output.read_text())["mechanics_policy"], "preserve")

    def test_rejects_donor_overwrite(self):
        template = Path(__file__).parents[1] / "research" / "templates" / "visual_variant_template.json"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                build(template, Path(td) / "variant.json", 2940001508)

    def test_rejects_malformed_transform(self):
        template = Path(__file__).parents[1] / "research" / "templates" / "visual_variant_template.json"
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "template.json"
            data = json.loads(template.read_text(encoding="utf-8"))
            data["scale"] = [1.0, 1.0]
            source.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "scale"):
                build(source, Path(td) / "variant.json", 3987654999)


if __name__ == "__main__":
    unittest.main()
