import unittest
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ProbeManifestSafetyTests(unittest.TestCase):
    def test_interaction_probe_generator_runs_as_cli(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_interaction_donor_probe.py"), "--help"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--resource-type", result.stdout)

    def test_every_research_probe_generator_declares_research_only(self):
        root = Path(__file__).resolve().parents[1]
        generators = (
            "build_behavior_probe.py",
            "build_item_visual_reference_probe.py",
            "build_kfc_research_probe.py",
            "build_kfc_write_probe.py",
            "build_visual_candidate_probe.py",
            "build_interaction_donor_probe.py",
        )
        for name in generators:
            source = (root / "tools" / name).read_text(encoding="utf-8")
            self.assertIn('"feature_state": "research-only"', source, name)

    def test_interaction_generator_rejects_quarantined_and_placeholder_donors(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "tools" / "build_interaction_donor_probe.py").read_text(encoding="utf-8")
        self.assertIn("TemplateResource", source)
        self.assertIn("donor-guid", source)
        self.assertIn("UUID", source)

    def test_building_catalog_probe_avoids_unsafe_type_userdata_enumeration(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "research" / "probes" / "building_catalog_resource_discovery_20260929" / "src" / "mod.lua").read_text(encoding="utf-8")
        self.assertNotIn("get_resource_types", source)
        self.assertNotIn("type_entry", source)
        self.assertIn("keen::VoxelBlueprintConfig", source)
        self.assertIn("get_resource_metadata_by_type", source)


if __name__ == "__main__":
    unittest.main()
