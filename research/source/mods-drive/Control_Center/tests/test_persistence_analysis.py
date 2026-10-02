import json
import tempfile
import unittest
from pathlib import Path

from core.persistence_analysis import PersistenceAnalyzer


class PersistenceAnalysisTests(unittest.TestCase):
    def test_unverified_content_is_research_only(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td); (project / "mod.json").write_text(json.dumps({
                "feature_state": "research-only", "content": [{"id": "demo:item", "numeric_id": 10}]
            }), encoding="utf-8")
            result = PersistenceAnalyzer().analyze(project)
            self.assertEqual(result.status, "research_only")
            self.assertEqual(result.stable_ids, (10,))
            self.assertTrue(result.requires_matching_clients)

    def test_server_missing_id_is_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td); (project / "mod.json").write_text(json.dumps({
                "game_build": "1076226", "content": [{"id": "demo:item", "numeric_id": 10}],
                "removal_policy": "migration_required"
            }), encoding="utf-8")
            result = PersistenceAnalyzer().analyze(project, {"build_id": "1076226", "content": []})
            self.assertEqual(result.status, "review_required")
            self.assertTrue(result.issues)


if __name__ == "__main__":
    unittest.main()
