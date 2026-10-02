import tempfile
import unittest
from pathlib import Path

from core.asset_pipeline import AssetPipeline


class AssetPipelineTests(unittest.TestCase):
    def test_inspects_png_and_plans_atlas(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + (64).to_bytes(4, "big") + (64).to_bytes(4, "big") + b"\x08\x06\x00\x00\x00"
            first = root / "b.png"; second = root / "a.png"; first.write_bytes(png); second.write_bytes(png)
            pipeline = AssetPipeline()
            one = pipeline.inspect(first, "icons")
            plan = pipeline.plan_icon_atlas([one, pipeline.inspect(second, "icons")], 64, 2)
            self.assertEqual((one.width, one.height), (64, 64))
            self.assertEqual(plan["rows"], 1)
            self.assertEqual(Path(plan["placements"][0]["asset"]).name, "a.png")

    def test_rejects_bad_png(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.png"; path.write_bytes(b"bad")
            with self.assertRaises(ValueError): AssetPipeline().inspect(path, "icons")

    def test_inspects_basic_model_containers_without_claiming_engine_import(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            glb = root / "mesh.glb"
            glb.write_bytes(b"glTF" + (2).to_bytes(4, "little") + (12).to_bytes(4, "little"))
            obj = root / "mesh.obj"
            obj.write_text("v 0 0 0\nf 1 1 1\n", encoding="utf-8")
            pipeline = AssetPipeline()
            self.assertEqual(pipeline.inspect(glb, "models").format, "glb")
            self.assertEqual(pipeline.inspect(obj, "models").format, "obj")
            self.assertEqual(pipeline.inspect(glb, "models").engine_status, "packaged-unverified-engine-import")


if __name__ == "__main__":
    unittest.main()
