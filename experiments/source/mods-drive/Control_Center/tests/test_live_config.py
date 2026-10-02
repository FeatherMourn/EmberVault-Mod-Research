import tempfile
import unittest
from pathlib import Path

from core.live_config import LiveConfigService


class LiveConfigTests(unittest.TestCase):
    def test_payload_contains_only_dynamic_settings(self):
        modules = {"sample": {"settings": [{"key": "speed", "dynamic": True}, {"key": "restart", "dynamic": False}]}}
        config = {"module_settings": {"sample": {"speed": 2, "restart": 9}}}
        payload = LiveConfigService().build_payload(modules, config)
        self.assertEqual(payload["modules"], {"sample": {"speed": 2}})

    def test_write_is_readable_and_atomic(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runtime_sync.json"
            service = LiveConfigService(); service.write(path, {}, {"module_settings": {}})
            self.assertEqual(service.read(path)["schema"], "control_center.live_config.v1")


if __name__ == "__main__":
    unittest.main()
