import json
import unittest
from pathlib import Path
from zipfile import ZipFile

from package_runtime_probes import package_probe


class RuntimePackagerTests(unittest.TestCase):
    def test_probe_zip_contains_loader_files(self):
        artifact = package_probe()
        with ZipFile(artifact) as archive:
            names = set(archive.namelist())
            self.assertIn("emberworks_worldwright_probe/mod.json", names)
            self.assertIn("emberworks_worldwright_probe/src/mod.lua", names)
            manifest = json.loads(archive.read("emberworks_worldwright_probe/mod.json"))
            self.assertEqual(manifest["capabilities"], ["patch", "export", "runtime-register-dll"])
            self.assertIn("emberworks_worldwright_probe/emberworks_native_bridge_probe.dll", names)


if __name__ == "__main__":
    unittest.main()
