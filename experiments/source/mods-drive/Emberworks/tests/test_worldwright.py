import unittest

from construction_sdk.models import Coordinate, Piece
from construction_sdk.operations import SimulatedWorld
from worldwright.engine import Selection, commit_batch, commit_plan, copy_selection, fill, paste_plan, preview_paste, replace, transform_blueprint
from construction_sdk.models import Transform
from zooping import wall


class WorldwrightTests(unittest.TestCase):
    def test_paste_reports_collision_and_undoes(self):
        source = [Piece(Coordinate(0, 0, 0), "wall", "stone"), Piece(Coordinate(1, 0, 0), "wall", "stone")]
        blueprint = copy_selection("test", source, Selection(Coordinate(0, 0, 0), Coordinate(1, 0, 0)))
        world = SimulatedWorld([Piece(Coordinate(11, 0, 0), "existing")])
        plan, blocked = paste_plan(blueprint, Coordinate(10, 0, 0), world)
        self.assertEqual(blocked, [Coordinate(11, 0, 0)])
        operation = commit_plan(world, plan)
        self.assertTrue(operation.undo(world))
        self.assertIsNone(world.inspect(Coordinate(10, 0, 0)))

    def test_fill_creates_complete_volume(self):
        blueprint = fill(Selection(Coordinate(0, 0, 0), Coordinate(1, 1, 1)), Piece(Coordinate(0, 0, 0), "stone"))
        self.assertEqual(len(blueprint.pieces), 8)

    def test_replace_is_transactional(self):
        world = SimulatedWorld([Piece(Coordinate(0, 0, 0), "wood"), Piece(Coordinate(1, 0, 0), "stone")])
        operation = replace(world, Selection(Coordinate(0, 0, 0), Coordinate(1, 0, 0)), "wood", Piece(Coordinate(0, 0, 0), "stone"))
        self.assertEqual(world.inspect(Coordinate(0, 0, 0)).resource_id, "stone")
        self.assertTrue(operation.undo(world))
        self.assertEqual(world.inspect(Coordinate(0, 0, 0)).resource_id, "wood")

    def test_preview_uses_shared_contract(self):
        blueprint = copy_selection("test", [Piece(Coordinate(0, 0, 0), "wall", "stone")],
                                   Selection(Coordinate(0, 0, 0), Coordinate(0, 0, 0)))
        world = SimulatedWorld([Piece(Coordinate(5, 0, 0), "existing")])
        preview = preview_paste(blueprint, Coordinate(5, 0, 0), world)
        self.assertEqual(preview.status, "blocked")
        self.assertEqual(preview.material_summary().counts, {"stone": 1})

    def test_paste_honors_procedural_anchor(self):
        blueprint = wall("wall", Coordinate(40, 3, 80), 2, 2, Piece(Coordinate(0, 0, 0), "wall" )).blueprint
        plan, blocked = paste_plan(blueprint, Coordinate(10, 5, 20), SimulatedWorld())
        self.assertEqual(blocked, [])
        self.assertEqual(sorted(plan), [Coordinate(10, 5, 20), Coordinate(10, 6, 20), Coordinate(11, 5, 20), Coordinate(11, 6, 20)])

    def test_transform_uses_procedural_anchor(self):
        blueprint = wall("wall", Coordinate(40, 3, 80), 2, 2, Piece(Coordinate(0, 0, 0), "wall")).blueprint
        rotated = transform_blueprint(blueprint, Transform(rotation=90))
        self.assertEqual(sorted(piece.position for piece in rotated.pieces),
                         [Coordinate(0, 0, 0), Coordinate(0, 0, 1), Coordinate(0, 1, 0), Coordinate(0, 1, 1)])

    def test_commit_batch_is_one_undoable_edit(self):
        world = SimulatedWorld()
        plans = []
        for x in (0, 1):
            blueprint = fill(Selection(Coordinate(0, 0, 0), Coordinate(0, 0, 0)), Piece(Coordinate(0, 0, 0), "stone"))
            plan, _ = paste_plan(blueprint, Coordinate(x, 0, 0), world)
            plans.append(plan)
        batch = commit_batch(world, plans, "zoop")
        self.assertEqual(len(batch.operations), 2)
        self.assertTrue(batch.undo(world))
        self.assertIsNone(world.inspect(Coordinate(0, 0, 0)))
        self.assertIsNone(world.inspect(Coordinate(1, 0, 0)))


if __name__ == "__main__":
    unittest.main()
