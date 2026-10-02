import tempfile
import unittest
from pathlib import Path

from blueprint_library import BlueprintLibrary
from builders_wand import WandTarget, plane
from chiselcraft import MicroStructure
from construction_sdk import Coordinate, OperationHistory, Piece, SimulatedWorld
from framed_architecture import AppearanceProfile, CompatibilityRegistry, FramedPiece, ShapeCatalog, to_blueprint
from kinetic_works.engine import Belt
from kinetic_works import KineticNetwork
from restoration.engine import compare, make_plan
from worldwright.engine import Selection, commit_batch, copy_selection, paste_plan
from zooping import floor


class EcosystemIntegrationTests(unittest.TestCase):
    def test_zoop_copy_paste_restore_and_history(self):
        source = SimulatedWorld()
        blueprint = floor("stone-floor", Coordinate(0, 0, 0), 2, 2,
                          Piece(Coordinate(0, 0, 0), "floor", "stone")).blueprint
        source = SimulatedWorld(blueprint.pieces)
        copied = copy_selection("copied-floor", blueprint.pieces,
                                Selection(Coordinate(0, 0, 0), Coordinate(1, 0, 1)))
        target = SimulatedWorld()
        plan, blocked = paste_plan(copied, Coordinate(5, 0, 5), target)
        self.assertFalse(blocked)
        batch = commit_batch(target, [plan], "worldwright-paste")
        history = OperationHistory()
        history.push(batch)
        self.assertIsNotNone(target.inspect(Coordinate(5, 0, 5)))
        repair = make_plan(compare(copied, target), "missing_only")
        self.assertGreaterEqual(len(repair.differences), 1)
        self.assertTrue(history.undo(target))

    def test_wand_chisel_and_framed_outputs_are_blueprints(self):
        wand_blueprint = plane("wand-plane", WandTarget(Coordinate(0, 0, 0), "wall"), 2, 2,
                               Piece(Coordinate(0, 0, 0), "wall", "stone"))
        self.assertEqual(len(wand_blueprint.pieces), 4)
        micro = MicroStructure("micro")
        micro.add_material("stone", "stone")
        micro.fill_box((0, 0, 0), (1, 1, 1), "stone")
        micro_blueprint = micro.to_blueprint(Coordinate(10, 0, 0))
        self.assertEqual(len(micro_blueprint.pieces), 8)
        catalog = ShapeCatalog()
        registry = CompatibilityRegistry()
        registry.register("stone", {"framed_panel"})
        framed = FramedPiece(Coordinate(0, 0, 0), "framed_panel", AppearanceProfile("stone", "glass"))
        framed_blueprint = to_blueprint("window", [framed], catalog, registry)
        self.assertEqual(framed_blueprint.pieces[0].material_id, "glass")

    def test_kinetic_layout_and_library_round_trip(self):
        belt = Belt("line", [(0, 0, 0), (1, 0, 0)])
        blueprint = belt.to_blueprint("kinetic:belt", "iron")
        self.assertEqual(len(blueprint.pieces), 2)
        with tempfile.TemporaryDirectory() as directory:
            library = BlueprintLibrary(Path(directory))
            saved = library.save(blueprint)
            loaded = library.load(saved.stem)
            self.assertEqual(loaded, blueprint)


if __name__ == "__main__":
    unittest.main()
