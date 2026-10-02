import tempfile
import unittest

from construction_sdk.models import Blueprint, Coordinate, Piece
from blueprint_library import BlueprintLibrary


class BlueprintLibraryTests(unittest.TestCase):
    def test_round_trip_and_search(self):
        with tempfile.TemporaryDirectory() as directory:
            library = BlueprintLibrary(directory)
            blueprint = Blueprint("Bridge", [Piece(Coordinate(0, 0, 0), "stone_wall", "stone")],
                                  metadata={"tags": ["bridge"]})
            path = library.save(blueprint)
            loaded = library.load(blueprint.blueprint_id)
            self.assertEqual(path.name, f"{blueprint.blueprint_id}.json")
            self.assertEqual(loaded.material_counts(), {"stone": 1})
            self.assertEqual(len(library.search("bridge", {"bridge"})), 1)

    def test_duplicate_positions_are_rejected(self):
        library = BlueprintLibrary(tempfile.mkdtemp())
        blueprint = Blueprint("Bad", [Piece(Coordinate(0, 0, 0), "a"), Piece(Coordinate(0, 0, 0), "b")])
        self.assertFalse(library.validate(blueprint).valid)

    def test_revisions_are_immutable_and_retrievable(self):
        with tempfile.TemporaryDirectory() as directory:
            library = BlueprintLibrary(directory)
            blueprint = Blueprint("Bridge", [Piece(Coordinate(0, 0, 0), "stone_wall")])
            library.save_revision(blueprint, 1)
            self.assertEqual(library.list_revisions(blueprint.blueprint_id), [1])
            loaded = library.load_revision(blueprint.blueprint_id, 1)
            self.assertEqual(loaded.name, "Bridge")
            with self.assertRaises(FileExistsError):
                library.save_revision(blueprint, 1)


if __name__ == "__main__":
    unittest.main()
