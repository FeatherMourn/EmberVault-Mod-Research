import json
import subprocess
import sys
import unittest
from pathlib import Path


class ResearchWorkerTests(unittest.TestCase):
    def test_worker_requires_research_profile(self):
        worker = Path(__file__).parents[1] / "src" / "research_worker.py"
        process = subprocess.run([sys.executable, str(worker), "--profile", "default"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(json.loads(process.stdout)["status"], "blocked")

    def test_worker_is_read_only_in_research_profile(self):
        worker = Path(__file__).parents[1] / "src" / "research_worker.py"
        process = subprocess.run([sys.executable, str(worker), "--profile", "research", "--operation", "EV-OP-1"], capture_output=True, text=True)
        payload = json.loads(process.stdout)
        self.assertEqual(process.returncode, 0)
        self.assertFalse(payload["data"]["mutates_workspace"])


if __name__ == "__main__":
    unittest.main()
