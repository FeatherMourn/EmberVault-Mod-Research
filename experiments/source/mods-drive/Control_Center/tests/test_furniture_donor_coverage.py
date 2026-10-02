from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_furniture_donor_coverage import verify


class FurnitureDonorCoverageTests(unittest.TestCase):
    def test_current_candidates_have_three_distinct_donors(self):
        result = verify(Path(__file__).parents[1] / "research" / "content_clone_candidates")
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(result["distinct_donor_count"], 3)
        self.assertEqual(result["runtime_registration_candidate_count"], 2)

    def test_duplicate_donor_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for index in range(3):
                (directory / f"{index}_candidate.json").write_text(
                    json.dumps({"donor": {"item_id": 123 if index else 123 + index}}),
                    encoding="utf-8",
                )
            result = verify(directory)
            self.assertFalse(result["valid"])
            self.assertTrue(any("distinct" in error for error in result["errors"]))

    def test_runtime_status_requires_an_existing_evidence_file(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for index in range(3):
                data = {"donor": {"item_id": index + 1}, "status": "DESIGN_ONLY_NOT_INJECTED"}
                if index == 1:
                    data.update({"status": "RUNTIME_REGISTRATION_PARTIAL_RESEARCH_ONLY", "runtime_evidence": "missing.json"})
                (directory / f"{index}_candidate.json").write_text(json.dumps(data), encoding="utf-8")
            result = verify(directory)
            self.assertFalse(result["valid"])
            self.assertTrue(any("runtime evidence file is missing" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
