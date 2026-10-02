import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_voxel_material_metadata_probe import build


class BuildVoxelMaterialMetadataProbeTests(unittest.TestCase):
    def test_builds_bounded_metadata_only_probe(self):
        donor = "11111111-2222-3333-4444-555555555555"
        values = ["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "99999999-8888-7777-6666-555555555555"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); archive = root / "voxel.zip"; output = root / "probe"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr(f"VoxelWorldResource/{donor}_x_0.json", json.dumps({"$guid": donor, "$part": 0, "materialGuids": [values[0], None, values[1], values[0]]}))
            result = build(archive, donor, 0, output)
            manifest = json.loads((output / "mod.json").read_text(encoding="utf-8"))
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
        self.assertEqual(result["guid_count"], 2)
        self.assertEqual(manifest["sample_count"], 2)
        self.assertEqual(manifest["mode"], "metadata-only-read-only")
        self.assertEqual(source.count("get_resource_metadata_by_guid(guid)"), 1)
        self.assertNotIn("get_resource(", source)
        self.assertNotIn("create_resource", source)

    def test_rejects_table_above_explicit_limit(self):
        donor = "11111111-2222-3333-4444-555555555555"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); archive = root / "voxel.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr(f"VoxelWorldResource/{donor}_x_0.json", json.dumps({"$guid": donor, "$part": 0, "materialGuids": ["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "99999999-8888-7777-6666-555555555555"]}))
            with self.assertRaisesRegex(ValueError, "above limit"):
                build(archive, donor, 0, root / "probe", max_guids=1)


if __name__ == "__main__": unittest.main()
