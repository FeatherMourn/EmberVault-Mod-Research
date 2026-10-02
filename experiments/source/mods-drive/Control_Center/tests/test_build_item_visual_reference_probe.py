import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class ItemVisualProbeTests(unittest.TestCase):
    def test_generates_non_mutating_probe(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "probe"
            r = subprocess.run([sys.executable, "tools/build_item_visual_reference_probe.py",
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "3987654601",
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", str(out)], cwd=ROOT,
                capture_output=True, text=True, check=True)
            m = json.loads((out / "mod.json").read_text())
            self.assertEqual(m["feature_state"], "research-only")
            self.assertFalse(m["runtime_mutation"])
            self.assertTrue((out / "src" / "mod.lua").exists())
if __name__ == "__main__": unittest.main()
