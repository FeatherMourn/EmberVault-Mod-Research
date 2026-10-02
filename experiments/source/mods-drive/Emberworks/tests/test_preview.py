import unittest

from construction_sdk import Coordinate, Piece, Preview


class PreviewTests(unittest.TestCase):
    def test_summary_and_status(self):
        preview = Preview("test")
        preview.add(Piece(Coordinate(0, 0, 0), "wall", "stone"))
        preview.add(Piece(Coordinate(1, 0, 0), "wall", "wood"), "warning", "substitution")
        self.assertEqual(preview.material_summary().counts, {"stone": 1, "wood": 1})
        self.assertEqual(preview.status, "warning")

    def test_blocked_preview_records_error(self):
        preview = Preview("test")
        preview.add(Piece(Coordinate(0, 0, 0), "wall"), "blocked", "collision")
        self.assertEqual(preview.status, "blocked")
        self.assertEqual(preview.errors, ["collision"])


if __name__ == "__main__":
    unittest.main()
