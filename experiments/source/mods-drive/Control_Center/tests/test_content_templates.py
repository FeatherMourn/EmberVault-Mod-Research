import json
import tempfile
import unittest
from pathlib import Path

from core.content_templates import ContentTemplateService


class ContentTemplateTests(unittest.TestCase):
    def test_template_declares_class_boundary_and_resources(self):
        template = ContentTemplateService().build("item", "My Mod", "Copper Sword")
        self.assertEqual(template["namespace"], "my_mod")
        self.assertEqual(template["feature_state"], "research-only")
        self.assertIn("ItemInfo", template["required_resource_types"])
        self.assertEqual(template["donor_metadata"], {})

    def test_template_write_is_atomic_json(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "template.json"
            ContentTemplateService().build("furniture_bed", "beds", "Palm Bed", destination)
            data = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(data["content_class"], "furniture_bed")
            self.assertEqual(data["schema"], "control_center.content_template.v1")


if __name__ == "__main__":
    unittest.main()
