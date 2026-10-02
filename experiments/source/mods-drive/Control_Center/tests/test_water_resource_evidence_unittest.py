import unittest
from pathlib import Path

from tools.verify_water_displacing_evidence import verify as verify_displacing
from tools.verify_water_chunk_metadata_evidence import verify as verify_chunk

ROOT = Path(__file__).resolve().parents[1]
BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class WaterResourceEvidenceTests(unittest.TestCase):
    def test_displacing_evidence(self):
        result = verify_displacing(ROOT / "research/probe_sessions/water_displacing_runtime_evidence_20260928.json", BUILD, "1.3")
        self.assertTrue(result["valid"], result["errors"])

    def test_chunk_metadata_evidence(self):
        result = verify_chunk(ROOT / "research/probe_sessions/water_chunk_metadata_runtime_evidence_20260928.json", BUILD, "1.3")
        self.assertTrue(result["valid"], result["errors"])

if __name__ == "__main__":
    unittest.main()
