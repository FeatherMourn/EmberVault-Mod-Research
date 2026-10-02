import re
import unittest
from pathlib import Path


class RetrofitAuditTests(unittest.TestCase):
    def test_status_matrix_covers_all_fifty_requested_upgrades(self):
        root = Path(__file__).parents[1]
        matrix = (root / "docs" / "RETROFIT_STATUS_MATRIX_20260926.md").read_text(encoding="utf-8")
        rows = {int(match.group(1)) for match in re.finditer(r"^\|\s*(\d+)\s*\|", matrix, re.MULTILINE)}
        self.assertEqual(rows, set(range(1, 51)))
        self.assertTrue((root / "docs" / "RETROFIT_COMPLETION_AUDIT_20260926.md").is_file())


if __name__ == "__main__":
    unittest.main()
