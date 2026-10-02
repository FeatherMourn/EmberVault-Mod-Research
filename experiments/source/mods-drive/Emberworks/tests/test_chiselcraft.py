import json
import unittest

from chiselcraft import MicroStructure
from chiselcraft.engine import edit_cells
from construction_sdk.models import Coordinate


class ChiselcraftTests(unittest.TestCase):
    def setUp(self):
        self.structure = MicroStructure("test")
        self.structure.add_material("stone", "stone_block")
        self.structure.add_material("wood", "wood_block")

    def test_cells_and_counts(self):
        self.structure.fill_box((0, 0, 0), (1, 1, 1), "stone")
        self.assertEqual(self.structure.material_counts(), {"stone": 8})

    def test_edit_undo_redo(self):
        operation = edit_cells(self.structure, [((0, 0, 0), "wood"), ((1, 0, 0), "stone")])
        operation.undo(self.structure)
        self.assertEqual(self.structure.cells, {})
        operation.redo(self.structure)
        self.assertEqual(self.structure.material_counts(), {"stone": 1, "wood": 1})

    def test_json_round_trip(self):
        self.structure.set_cell((15, 15, 15), "wood")
        restored = MicroStructure.from_dict(json.loads(json.dumps(self.structure.to_dict())))
        self.assertEqual(restored.cells, self.structure.cells)

    def test_out_of_bounds_rejected(self):
        with self.assertRaises(ValueError):
            self.structure.set_cell((16, 0, 0), "stone")

    def test_exports_shared_blueprint(self):
        self.structure.set_cell((2, 3, 4), "wood")
        blueprint = self.structure.to_blueprint(Coordinate(10, 20, 30))
        self.assertEqual(blueprint.source_type, "chiselcraft")
        self.assertEqual(blueprint.pieces[0].position, Coordinate(12, 23, 34))
        self.assertEqual(blueprint.pieces[0].resource_id, "wood_block")


if __name__ == "__main__":
    unittest.main()
