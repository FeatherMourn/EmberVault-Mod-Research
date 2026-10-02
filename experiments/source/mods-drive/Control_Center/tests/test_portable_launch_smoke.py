import unittest
from pathlib import Path

from tools.verify_portable_launch_smoke import validate


class PortableLaunchSmokeTests(unittest.TestCase):
    def test_current_evidence_is_valid(self):
        path = Path(__file__).resolve().parents[1] / "research" / "PORTABLE_LAUNCH_SMOKE_20260928.json"
        result = validate(path)
        self.assertTrue(result["valid"], result)


if __name__ == "__main__":
    unittest.main()
