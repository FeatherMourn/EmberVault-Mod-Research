import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("scan_inventory_transfer_static_map.py")
SPEC = importlib.util.spec_from_file_location("inventory_static_map", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class StaticMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = MODULE_PATH.resolve().parents[4]
        cls.image = MODULE.Image(root / "enshrouded.exe")
        cls.report = MODULE.build_report(cls.image)

    def test_all_action_fields_are_present_once(self):
        fields = self.report["actionCandidate"]["fields"]
        self.assertEqual([row["offset"] for row in fields],
                         ["+0x00", "+0x04", "+0x08", "+0x0C", "+0x14", "+0x1C", "+0x1D", "+0x1E"])

    def test_connected_calls_are_current_build_bytes(self):
        self.assertEqual(self.image.bytes_at(0x37200D, 5), bytes.fromhex("E8 6E 41 01 00"))
        self.assertEqual(self.image.bytes_at(0x372020, 5), bytes.fromhex("E8 5B 3D 01 00"))

    def test_report_is_json_serializable_and_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(self.report, sort_keys=True), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(loaded["safety"]["processAccess"])
        self.assertFalse(loaded["safety"]["writesExecutable"])


if __name__ == "__main__":
    unittest.main()
