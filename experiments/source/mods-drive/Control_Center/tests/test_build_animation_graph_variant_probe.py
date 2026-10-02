import json
import tempfile
import unittest
from pathlib import Path
from tools.build_animation_graph_variant_probe import build

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"research"/"templates"/"animation_graph_variant_template.json"

class AnimationGraphVariantProbeGeneratorTests(unittest.TestCase):
    def test_generates_research_only_bounded_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"probe";manifest=build(TEMPLATE,output);source=(output/"src"/"mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["feature_state"],"research-only");self.assertTrue(manifest["rollback_required"]);self.assertIn("animation_graph_variant_attached",source);self.assertIn("animationPayload=false",source)
    def test_rejects_donor_guid_reuse(self):
        data=json.loads(TEMPLATE.read_text(encoding="utf-8"));data["clone_guid"]=data["donor_guid"]
        with tempfile.TemporaryDirectory() as directory:
            definition=Path(directory)/"definition.json";definition.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"clone_guid must differ"): build(definition,Path(directory)/"probe")
    def test_rejects_template_owner(self):
        data=json.loads(TEMPLATE.read_text(encoding="utf-8"));data["owner"]["type"]="keen::TemplateResource"
        with tempfile.TemporaryDirectory() as directory:
            definition=Path(directory)/"definition.json";definition.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"owner type"): build(definition,Path(directory)/"probe")
