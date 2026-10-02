import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "research" / "probes" / "voxel_material_guid_type_probe_1076226"


class VoxelMaterialGuidProbeContractTests(unittest.TestCase):
    def test_manifest_is_metadata_only_and_build_pinned(self):
        data = json.loads((PROBE / "mod.json").read_text(encoding="utf-8"))
        self.assertEqual(data["mode"], "metadata-only-read-only")
        self.assertEqual(data["required_loader_api_version"], "1.3")
        self.assertEqual(data["compatible_game_builds"], ["1076226"])
        self.assertTrue(data["research_only"])

    def test_source_never_decodes_or_mutates_payloads(self):
        source = (PROBE / "src" / "mod.lua").read_text(encoding="utf-8")
        self.assertEqual(source.count("get_resource_metadata_by_guid(guid)"), 1)
        self.assertEqual(source.count("'d0122ac2-e754-6d46-a4f6-8ef1e3844253'"), 1)
        self.assertIn("payload=false|created=false|registered=false|mutated=false|world=false|save=false", source)
        self.assertNotIn("get_resource(", source)
        self.assertNotIn("create_resource", source)
        self.assertNotIn("register_resource", source)


if __name__ == "__main__":
    unittest.main()
