import re
import unittest
from pathlib import Path


class RetrofitMatrixTests(unittest.TestCase):
    def test_matrix_contains_exactly_fifty_unique_upgrade_rows(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "RETROFIT_STATUS_MATRIX_20260926.md"
        )
        text = path.read_text(encoding="utf-8")
        rows = [int(n) for n in re.findall(r"^\|\s*(\d+)\s*\|", text, re.MULTILINE)]
        self.assertEqual(rows, list(range(1, 51)))


if __name__ == "__main__":
    unittest.main()
