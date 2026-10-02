import unittest

from builders_wand import WandLimits, WandTarget, column, plane, row
from construction_sdk.models import Coordinate, Piece


class WandTests(unittest.TestCase):
    target = WandTarget(Coordinate(10, 20, 30)).pin()
    prototype = Piece(Coordinate(0, 0, 0), "wood_wall", "wood")

    def test_pinned_row(self):
        blueprint = row("row", self.target, 4, self.prototype)
        self.assertTrue(self.target.pinned)
        self.assertEqual(len(blueprint.pieces), 4)
        self.assertEqual(blueprint.material_counts(), {"wood": 4})

    def test_column_and_plane(self):
        self.assertEqual(len(column("column", self.target, 3, self.prototype).pieces), 3)
        self.assertEqual(len(plane("plane", self.target, 3, 2, self.prototype).pieces), 6)

    def test_limits_are_enforced(self):
        with self.assertRaises(ValueError):
            row("too-big", self.target, 5, self.prototype, limits=WandLimits(max_pieces=4, max_distance=4))


if __name__ == "__main__":
    unittest.main()
