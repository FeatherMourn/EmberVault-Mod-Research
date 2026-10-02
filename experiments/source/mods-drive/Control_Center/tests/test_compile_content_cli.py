import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CompileContentCliTests(unittest.TestCase):
    def test_cli_compiles_definition_with_relative_icon(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            work = Path(td); base = work / "control"; definition_dir = work / "definition"
            (base / "profiles").mkdir(parents=True); (base / "research" / "runtime").mkdir(parents=True); definition_dir.mkdir()
            for name in ("kfc_content_registry.lua", "kfc_localization_registry.lua"):
                (base / "research" / "runtime" / name).write_text("return {}", encoding="utf-8")
            (definition_dir / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\ncli")
            definition = {
                "namespace": "cli_demo", "id": "cli_bed", "name": "CLI Bed", "author": "Tester",
                "definition_dir": str(definition_dir), "icon": "icon.png",
            }
            definition_path = definition_dir / "definition.json"
            definition_path.write_text(json.dumps(definition), encoding="utf-8")
            output = work / "output"
            result = subprocess.run([
                sys.executable, str(root / "tools" / "compile_content_definition.py"),
                str(definition_path), str(output), "--base-dir", str(base),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "assets" / "icons" / "icon.png").is_file())
            self.assertEqual(json.loads(result.stdout)["status"], "research-only")


if __name__ == "__main__":
    unittest.main()
