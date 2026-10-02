import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_blender_runtime_log import verify


class BlenderRuntimeLogTests(unittest.TestCase):
    def test_required_markers_are_verified(self):
        markers = [
            "custom texture: a", "assigned custom material: a", "EBT DEBUG item registry=x",
            "EBT DEBUG recipe registry=x", "EBT DEBUG recipe UI added", "patched RenderModel; content=x",
            "Attaching runtime loader",
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "session.eml.log"
            path.write_text("\n".join(json.dumps({"fields": {"message": f"[stool] {m}"}}) for m in markers), encoding="utf-8")
            result = verify(path)
            self.assertTrue(result["valid"], result)

    def test_missing_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "session.eml.log"
            path.write_text(json.dumps({"fields": {"message": "[stool] loading"}}), encoding="utf-8")
            self.assertFalse(verify(path)["valid"])


if __name__ == "__main__":
    unittest.main()
