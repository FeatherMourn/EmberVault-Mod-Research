import hashlib
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from core.blender_export_validator import validate_blender_export
from core.local_mods import LocalModService


class BlenderExportValidatorTests(unittest.TestCase):
    def test_valid_export_is_research_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "textures").mkdir()
            mesh = b"render-data"; (root / "render_data.bin").write_bytes(mesh); (root / "src" / "mod.lua").write_text("-- probe")
            validation = {"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": len(mesh), "mesh_sha256": hashlib.sha256(mesh).hexdigest(), "vertex_count": 3, "vertex_stride": 24, "texture_patches": []}
            (root / "validation.json").write_text(json.dumps(validation)); (root / "mod.json").write_text(json.dumps({"id": "demo"}))
            result = validate_blender_export(root)
            self.assertTrue(result["valid"]); self.assertEqual(result["feature_state"], "research-only")
            self.assertEqual(result["lod_metadata_status"], "not provided")
            self.assertEqual(result["collider_metadata_status"], "not provided")

    def test_full_topology_vertex_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 65536, "vertex_stride": 24}))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"])
            self.assertIn("65,535", " ".join(result["errors"]))
            self.assertTrue(any("Reduce the generated mesh" in step for step in result["next_steps"]))

    def test_unsupported_collider_shape_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24, "colliders": [{"shape": "Mesh"}]}))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"])
            self.assertIn("unsupported collider shape", " ".join(result["errors"]))

    def test_lod_vertex_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24, "lods": [{"name": "lod1", "vertex_count": 70000}]}))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"])
            self.assertIn("LOD vertex_count", " ".join(result["errors"]))

    def test_command_line_validator_reports_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24}))
            completed = subprocess.run([sys.executable, "tools/verify_blender_export.py", str(root)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0)
            self.assertTrue(json.loads(completed.stdout)["valid"])

    def test_tampered_mesh_fails_hash_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"changed"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 3, "mesh_sha256": "bad", "vertex_count": 1, "vertex_stride": 24}))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"]); self.assertIn("mesh_sha256", " ".join(result["errors"]))
            self.assertTrue(result["next_steps"])

    def test_declared_target_must_be_referenced_by_generated_lua(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x")
            (root / "src" / "mod.lua").write_text("local MODEL_GUID = 'wrong'\n", encoding="utf-8")
            (root / "mod.json").write_text('{"id":"demo"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "target_type": "keen::RenderModel", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24}))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"])
            self.assertIn("target_guid", " ".join(result["errors"]))

    def test_valid_export_enters_local_mod_preview_without_installing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo","name":"Demo","version":"0.1.0"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24}))
            service = LocalModService(root / "library")
            package = service.inspect(root)
            preview = service.preview(package, root / "game")
            self.assertEqual(package.status, "recognized and supported")
            self.assertTrue(preview["target"].endswith("mods\\demo") or preview["target"].endswith("mods/demo"))
            self.assertFalse((root / "game" / "mods").exists())

    def test_non_research_export_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo","feature_state":"stable"}')
            (root / "validation.json").write_text(json.dumps({"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24}))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"])
            self.assertIn("research-only", " ".join(result["errors"]))
            self.assertTrue(result["next_steps"])

    def test_texture_patch_cannot_escape_export_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "src").mkdir(); (root / "textures").mkdir(); (root / "render_data.bin").write_bytes(b"x"); (root / "src" / "mod.lua").write_text("--")
            (root / "mod.json").write_text('{"id":"demo"}')
            validation = {"target_guid": "98b0ca77-872a-492d-b051-9b06fc8f495c", "mesh_size": 1, "mesh_sha256": hashlib.sha256(b"x").hexdigest(), "vertex_count": 1, "vertex_stride": 24, "texture_patches": [{"material_index": "0", "material_guid": "guid", "slot": "../../../../escape", "sha256": ""}]}
            (root / "validation.json").write_text(json.dumps(validation))
            result = validate_blender_export(root)
            self.assertFalse(result["valid"])
            self.assertIn("escapes", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
