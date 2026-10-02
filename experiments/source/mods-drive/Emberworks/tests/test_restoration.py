import unittest

from construction_sdk.models import Blueprint, Coordinate, Piece
from construction_sdk.operations import SimulatedWorld
from restoration import compare, make_plan
from restoration.engine import apply_plan, apply_plan_operation


class RestorationTests(unittest.TestCase):
    def test_classifies_missing_wrong_material_and_unexpected(self):
        reference = Blueprint("ref", [Piece(Coordinate(0, 0, 0), "wall", "stone"), Piece(Coordinate(1, 0, 0), "wall", "stone")])
        world = SimulatedWorld([Piece(Coordinate(1, 0, 0), "wall", "wood"), Piece(Coordinate(2, 0, 0), "extra")])
        differences = compare(reference, world)
        self.assertEqual({d.classification for d in differences}, {"missing_piece", "wrong_material", "unexpected_piece"})

    def test_missing_only_plan_preserves_unexpected(self):
        reference = Blueprint("ref", [Piece(Coordinate(0, 0, 0), "wall", "stone")])
        world = SimulatedWorld([Piece(Coordinate(2, 0, 0), "extra")])
        plan = make_plan(compare(reference, world), "missing_only")
        before = apply_plan(world, plan)
        self.assertEqual(len(before), 1)
        self.assertEqual(world.inspect(Coordinate(0, 0, 0)).material_id, "stone")
        self.assertEqual(world.inspect(Coordinate(2, 0, 0)).resource_id, "extra")

    def test_substitution_counts(self):
        reference = Blueprint("ref", [Piece(Coordinate(0, 0, 0), "wall", "stone")])
        plan = make_plan(compare(reference, SimulatedWorld()), "missing_only", {"stone": "reinforced_stone"})
        self.assertEqual(plan.material_counts, {"reinforced_stone": 1})

    def test_apply_returns_shared_undoable_operation(self):
        reference = Blueprint("ref", [Piece(Coordinate(0, 0, 0), "wall", "stone")])
        world = SimulatedWorld()
        plan = make_plan(compare(reference, world), "missing_only")
        operation = apply_plan_operation(world, plan)
        self.assertEqual(world.inspect(Coordinate(0, 0, 0)).resource_id, "wall")
        self.assertTrue(operation.undo(world))
        self.assertIsNone(world.inspect(Coordinate(0, 0, 0)))
        self.assertTrue(operation.redo(world))


if __name__ == "__main__":
    unittest.main()
