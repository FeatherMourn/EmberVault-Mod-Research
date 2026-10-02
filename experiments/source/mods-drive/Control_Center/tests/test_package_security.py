import json
import tempfile
import unittest
from pathlib import Path

from core.package_security import PackageSecurityService


class PackageSecurityTests(unittest.TestCase):
    def test_lock_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "package"; package.mkdir()
            (package / "mod.json").write_text(json.dumps({"id": "demo", "version": "1.0.0", "author": "Tester"}), encoding="utf-8")
            payload = package / "mod.lua"; payload.write_text("return {}", encoding="utf-8")
            service = PackageSecurityService()
            service.create_lock(package, license_name="MIT", build_fingerprint="abc")
            self.assertTrue(service.verify(package).valid)
            payload.write_text("tampered", encoding="utf-8")
            result = service.verify(package)
            self.assertFalse(result.valid)
            self.assertTrue(any("hash mismatch" in issue for issue in result.errors))

    def test_new_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "package"; package.mkdir()
            (package / "mod.json").write_text(json.dumps({"id": "demo", "version": "1.0.0"}), encoding="utf-8")
            service = PackageSecurityService(); service.create_lock(package)
            (package / "extra.txt").write_text("extra", encoding="utf-8")
            self.assertFalse(service.verify(package).valid)


if __name__ == "__main__":
    unittest.main()
