import unittest
from unittest.mock import patch

from tools import verify_milestone


class VerifyMilestoneRunnerTests(unittest.TestCase):
    def test_gate_timeout_is_structured_failure(self):
        with patch("tools.verify_milestone.subprocess.run", side_effect=verify_milestone.subprocess.TimeoutExpired(["fake"], 180, output="partial", stderr="hung")):
            result = verify_milestone.run("hung_gate", ["fake"])
        self.assertFalse(result["passed"])
        self.assertIsNone(result["returncode"])
        self.assertIn("Timed out", result["stderr_tail"])
