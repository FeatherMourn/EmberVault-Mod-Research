import unittest

from construction_sdk import BatchOperation, Coordinate, OperationHistory, Piece, SimulatedWorld
from worldwright.engine import Selection, commit_plan, fill, paste_plan


class OperationHistoryTests(unittest.TestCase):
    def test_undo_redo_and_new_operation_clear_redo(self):
        world = SimulatedWorld()
        history = OperationHistory(limit=2)
        for x in (0, 1):
            blueprint = fill(Selection(Coordinate(x, 0, 0), Coordinate(x, 0, 0)), Piece(Coordinate(0, 0, 0), "stone"))
            plan, blocked = paste_plan(blueprint, Coordinate(x, 0, 0), world)
            self.assertFalse(blocked)
            history.push(commit_plan(world, plan, "fill"))
        self.assertEqual(history.undo_depth, 2)
        self.assertTrue(history.undo(world))
        self.assertEqual(history.redo_depth, 1)
        self.assertTrue(history.redo(world))
        self.assertEqual(history.redo_depth, 0)
        blueprint = fill(Selection(Coordinate(2, 0, 0), Coordinate(2, 0, 0)), Piece(Coordinate(0, 0, 0), "stone"))
        plan, _ = paste_plan(blueprint, Coordinate(0, 0, 0), world)
        history.push(commit_plan(world, plan, "fill"))
        self.assertEqual(history.redo_depth, 0)

    def test_batch_undoes_as_one_edit(self):
        world = SimulatedWorld()
        operations = []
        for x in (0, 1):
            piece = Piece(Coordinate(x, 0, 0), "stone")
            operations.append(commit_plan(world, {piece.position: piece}, "piece"))
        history = OperationHistory()
        history.push(BatchOperation("zoop", operations))
        self.assertTrue(history.undo(world))
        self.assertIsNone(world.inspect(Coordinate(0, 0, 0)))
        self.assertIsNone(world.inspect(Coordinate(1, 0, 0)))
        self.assertTrue(history.redo(world))


if __name__ == "__main__":
    unittest.main()
