import unittest

from construction_sdk.models import Coordinate, Piece
from zooping import bridge, column, floor, repeat, wall


class ZoopingTests(unittest.TestCase):
    prototype = Piece(Coordinate(0, 0, 0), "stone_wall", "stone")

    def test_wall_count_and_materials(self):
        operation = wall("wall", Coordinate(0, 0, 0), 4, 3, self.prototype)
        self.assertEqual(operation.requested, 12)
        self.assertEqual(operation.blueprint.material_counts(), {"stone": 12})

    def test_floor_and_column_counts(self):
        self.assertEqual(floor("floor", Coordinate(0, 0, 0), 3, 2, self.prototype).requested, 6)
        self.assertEqual(column("column", Coordinate(0, 0, 0), 5, self.prototype).requested, 5)

    def test_bridge_and_repeat(self):
        self.assertEqual(bridge("bridge", Coordinate(0, 0, 0), 4, 2, self.prototype).requested, 8)
        source = floor("source", Coordinate(0, 0, 0), 2, 1, self.prototype).blueprint
        self.assertEqual(repeat("repeat", source, 3, Coordinate(0, 0, 2)).requested, 6)


if __name__ == "__main__":
    unittest.main()
