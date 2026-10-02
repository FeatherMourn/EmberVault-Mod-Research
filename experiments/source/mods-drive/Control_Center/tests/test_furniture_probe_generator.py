from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "research" / "probes" / "bed_clone_injection_1076226"
GENERATOR = ROOT / "tools" / "build_furniture_clone_probe.py"


class FurnitureProbeGeneratorTests(unittest.TestCase):
    def test_generator_retargets_a_non_bed_template(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bench_probe"
            subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    str(ROOT / "research" / "probes" / "chair_stool_clone_1076226"),
                    str(output),
                    "2380198378",
                    "1960127880",
                    "3987658001",
                    "3987658002",
                    "CC Custom Bench 001",
                    "--log-prefix",
                    "[CC-BENCH-CLONE] ",
                ],
                cwd=ROOT,
                check=True,
            )
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("local DONOR_ID = 2380198378", source)
            self.assertIn('clone.data.debugName = "CC Custom Bench 001"', source)
            self.assertIn("value == 1960127880", source)

    def test_custom_log_marker_is_written_for_non_bed_donor(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "chair_probe"
            result = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    str(TEMPLATE),
                    str(output),
                    "14195262",
                    "1355882648",
                    "3987654703",
                    "3987654704",
                    "CC_Custom_Chair_Stool_002",
                    "--log-prefix",
                    "[CC-FURNITURE-CLONE] ",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Generated furniture clone probe", result.stdout)
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn('local PREFIX = "[CC-FURNITURE-CLONE] "', source)
            manifest = json.loads((output / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["donor_item_id"], 14195262)
            self.assertEqual(manifest["new_item_id"], 3987654703)

    def test_existing_default_marker_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bed_probe"
            subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    str(TEMPLATE),
                    str(output),
                    "2940001508",
                    "3531872774",
                    "3987654705",
                    "3987654706",
                    "CC_Custom_Bed_002",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn('local PREFIX = "[CC-BED-CLONE] "', source)


if __name__ == "__main__":
    unittest.main()
