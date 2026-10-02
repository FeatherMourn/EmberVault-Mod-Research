import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.analyze_voxel_world_dependencies import SCHEMA, analyze


class VoxelWorldDependencyAnalysisTests(unittest.TestCase):
    def test_maps_scene_ownership_materials_and_content_hashes(self):
        guid = "11111111-2222-3333-4444-555555555555"
        standalone = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            voxel = root / "voxel.zip"
            scene = root / "scene.zip"
            with zipfile.ZipFile(scene, "w") as archive:
                archive.writestr(f"SceneResource/{guid}_x_0.json", "{}")
            base = {
                "type": "Solid", "size": {"x": 1, "y": 2, "z": 3},
                "materialGuids": ["99999999-8888-7777-6666-555555555555", None],
                "voxelLevels": [{"tiles": [{"size": 12, "hash0": 1, "hash1": 2, "hash2": 3}]}],
                "cpuDisplacement": {"size": 0, "hash0": 0, "hash1": 0, "hash2": 0},
                "voxelHashes": {"size": 0, "hash0": 0, "hash1": 0, "hash2": 0},
            }
            with zipfile.ZipFile(voxel, "w") as archive:
                for current in (guid, standalone):
                    payload = dict(base, **{"$guid": current, "$part": 0})
                    archive.writestr(f"VoxelWorldResource/{current}_x_0.json", json.dumps(payload))
            result = analyze(voxel, scene)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["world_count"], 2)
        self.assertEqual(result["scene_owned_world_count"], 1)
        self.assertEqual(result["standalone_world_count"], 1)
        self.assertEqual(result["unique_material_guid_count"], 1)
        self.assertEqual(result["unique_content_hash_count"], 1)
        self.assertEqual(result["referenced_content_bytes"], 12)

    def test_detects_multiple_parts_for_one_world_guid(self):
        guid = "11111111-2222-3333-4444-555555555555"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            voxel = root / "voxel.zip"
            scene = root / "scene.zip"
            with zipfile.ZipFile(scene, "w") as archive:
                archive.writestr("placeholder.txt", "")
            with zipfile.ZipFile(voxel, "w") as archive:
                for part in (0, 1):
                    archive.writestr(
                        f"VoxelWorldResource/{guid}_x_{part}.json",
                        json.dumps({"$guid": guid, "$part": part, "type": "Solid", "size": {},
                                    "materialGuids": [], "voxelLevels": []}),
                    )
            result = analyze(voxel, scene)
        self.assertEqual(result["multi_part_world_guids"], [{"guid": guid, "parts": [0, 1]}])


if __name__ == "__main__":
    unittest.main()
