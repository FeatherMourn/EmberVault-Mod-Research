import tempfile
import unittest
from pathlib import Path
from tools.verify_multiplayer_authority_report import validate

class MultiplayerAuthorityReportTests(unittest.TestCase):
    def test_current_report_is_complete_and_conservative(self):
        path = Path(__file__).parents[1] / "research" / "MULTIPLAYER_AUTHORITY_FEASIBILITY_20260928.md"
        self.assertEqual(validate(path), [])

    def test_report_rejects_missing_peer_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            path.write_text("## Findings\n## Safe product policy\n## Conclusion\nremains unsupported", encoding="utf-8")
            self.assertTrue(any("missing required" in error for error in validate(path)))

if __name__ == "__main__":
    unittest.main()
