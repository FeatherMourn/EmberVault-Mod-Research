import unittest
from pathlib import Path


class NativeBridgeSourceTests(unittest.TestCase):
    def test_probe_is_inert_and_configured_as_cdylib(self):
        root = Path(__file__).parents[1] / "native_bridge_probe"
        cargo = (root / "Cargo.toml").read_text(encoding="utf-8")
        source = (root / "src" / "lib.rs").read_text(encoding="utf-8")
        self.assertIn('crate-type = ["cdylib"]', cargo)
        self.assertIn("emberworks_bridge_version", source)
        self.assertNotIn("CreateRemoteThread", source)
        self.assertNotIn("WriteProcessMemory", source)


if __name__ == "__main__":
    unittest.main()
